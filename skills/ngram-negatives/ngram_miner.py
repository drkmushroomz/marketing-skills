#!/usr/bin/env python3
"""
N-Gram Negative Keyword Miner for Google Ads.

Pulls search term data from the Google Ads API, runs 1-word n-gram analysis,
identifies wasted spend terms with no conversions, and posts recommendations
to Slack for approval. Approved terms get applied as negative keywords.

Usage:
  # Mine and post to Slack:
  python ngram_miner.py --mode mine

  # Apply approved negatives (called after Slack approval):
  python ngram_miner.py --mode apply --keyword "badterm" --campaign-id 123456

  # Check for approval responses in Slack:
  python ngram_miner.py --mode check-approvals
"""

import argparse
import json
import os
import sys
import re
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
STATE_PATH = SCRIPT_DIR / "state.json"
ENV_PATH = SCRIPT_DIR.parent.parent.parent / ".env"

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "are",
    "this", "that", "my", "your", "i", "me", "we", "you", "he", "she",
    "his", "her", "our", "their", "its", "do", "does", "did", "has",
    "have", "had", "will", "would", "can", "could", "how", "what",
    "when", "where", "who", "which", "not", "no", "so", "if", "up",
    "out", "about", "just", "more", "also", "than", "then", "into",
    "over", "after", "before", "between", "through", "during", "been",
    "being", "am", "were", "get", "got", "vs", "s", "t", "re", "ve",
    "ll", "d", "m", "don", "doesn", "didn", "won", "wouldn", "couldn",
}


def load_env():
    """Load .env file into a dict."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip()
    return env


def load_config():
    return json.loads(CONFIG_PATH.read_text())


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_run": None, "pending_approvals": {}, "applied": [], "dismissed": []}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Google Ads API
# ---------------------------------------------------------------------------
def get_google_ads_client(env, config):
    from google.ads.googleads.client import GoogleAdsClient

    credentials_config = {
        "developer_token": env["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": env["GOOGLE_OAUTH_CLIENT_ID"],
        "client_secret": env["GOOGLE_OAUTH_CLIENT_SECRET"],
        "login_customer_id": config["mcc_id"],
        "use_proto_plus": True,
    }

    # Use the dedicated Google Ads refresh token (has adwords scope)
    if "GOOGLE_ADS_REFRESH_TOKEN" in env:
        credentials_config["refresh_token"] = env["GOOGLE_ADS_REFRESH_TOKEN"]
    else:
        print("ERROR: No GOOGLE_ADS_REFRESH_TOKEN in .env. Run get_refresh_token.py first.", file=sys.stderr)
        sys.exit(1)

    return GoogleAdsClient.load_from_dict(credentials_config)


def fetch_search_terms(client, customer_id, lookback_days):
    """Fetch search term report for the last N days."""
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    query = f"""
        SELECT
            search_term_view.search_term,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY metrics.cost_micros DESC
    """

    results = []
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in response:
        for row in batch.results:
            results.append({
                "search_term": row.search_term_view.search_term,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": row.metrics.conversions,
            })
    return results


def get_existing_negatives(client, customer_id):
    """Fetch all existing negative keywords to avoid duplicates."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            campaign_criterion.keyword.text,
            campaign_criterion.keyword.match_type,
            campaign_criterion.campaign
        FROM campaign_criterion
        WHERE campaign_criterion.type = 'KEYWORD'
          AND campaign_criterion.negative = TRUE
    """

    negatives = set()
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in response:
            for row in batch.results:
                negatives.add(row.campaign_criterion.keyword.text.lower())
    except Exception:
        pass  # If no negatives exist yet, that's fine

    return negatives


def get_or_create_shared_neg_list(client, customer_id, list_name="N-Gram Negatives"):
    """Get or create a shared negative keyword list at the account level."""
    ga_service = client.get_service("GoogleAdsService")

    # Check if the list already exists
    query = f"""
        SELECT shared_set.id, shared_set.name
        FROM shared_set
        WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
          AND shared_set.name = '{list_name}'
          AND shared_set.status = 'ENABLED'
    """
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        return row.shared_set.id

    # Create it
    shared_set_service = client.get_service("SharedSetService")
    operation = client.get_type("SharedSetOperation")
    shared_set = operation.create
    shared_set.name = list_name
    shared_set.type_ = client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS

    response = shared_set_service.mutate_shared_sets(
        customer_id=customer_id,
        operations=[operation],
    )
    resource_name = response.results[0].resource_name
    # Extract ID from resource name (format: customers/{id}/sharedSets/{id})
    shared_set_id = int(resource_name.split("/")[-1])

    # Link the shared set to all active search/shopping campaigns
    link_shared_set_to_campaigns(client, customer_id, resource_name)

    return shared_set_id


def link_shared_set_to_campaigns(client, customer_id, shared_set_resource):
    """Link a shared negative keyword list to all active search/shopping campaigns."""
    ga_service = client.get_service("GoogleAdsService")
    campaign_shared_set_service = client.get_service("CampaignSharedSetService")

    # Get all active campaigns
    query = """
        SELECT campaign.id, campaign.name, campaign.resource_name
        FROM campaign
        WHERE campaign.status = 'ENABLED'
          AND campaign.advertising_channel_type IN ('SEARCH', 'SHOPPING', 'PERFORMANCE_MAX')
    """

    # Check which campaigns already have this shared set linked
    link_query = f"""
        SELECT campaign.id
        FROM campaign_shared_set
        WHERE shared_set.resource_name = '{shared_set_resource}'
    """
    already_linked = set()
    try:
        response = ga_service.search(customer_id=customer_id, query=link_query)
        for row in response:
            already_linked.add(row.campaign.id)
    except Exception:
        pass

    operations = []
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        if row.campaign.id in already_linked:
            continue
        operation = client.get_type("CampaignSharedSetOperation")
        css = operation.create
        css.campaign = row.campaign.resource_name
        css.shared_set = shared_set_resource
        operations.append(operation)

    if operations:
        campaign_shared_set_service.mutate_campaign_shared_sets(
            customer_id=customer_id,
            operations=operations,
        )
        print(f"  Linked shared neg list to {len(operations)} campaigns")


def apply_negative_keyword(client, customer_id, campaign_id, keyword, match_type="EXACT"):
    """Apply a negative keyword to the account-level shared negative keyword list."""
    list_name = "N-Gram Negatives"
    shared_set_id = get_or_create_shared_neg_list(client, customer_id, list_name)

    shared_criterion_service = client.get_service("SharedCriterionService")
    shared_set_resource = client.get_service("SharedSetService").shared_set_path(customer_id, shared_set_id)

    operation = client.get_type("SharedCriterionOperation")
    criterion = operation.create
    criterion.shared_set = shared_set_resource
    criterion.keyword.text = keyword
    criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type].value

    response = shared_criterion_service.mutate_shared_criteria(
        customer_id=customer_id,
        operations=[operation],
    )
    return response.results[0].resource_name


# ---------------------------------------------------------------------------
# N-Gram Analysis
# ---------------------------------------------------------------------------
def analyze_ngrams(search_terms, ngram_size=1, min_impressions=10, max_conversions=0, min_spend=0):
    """
    Break search terms into 1-word n-grams and aggregate metrics.
    Return terms that have spend but no conversions.
    """
    ngram_data = defaultdict(lambda: {
        "impressions": 0,
        "clicks": 0,
        "cost": 0.0,
        "conversions": 0.0,
        "search_terms": set(),
        "campaigns": set(),
    })

    for st in search_terms:
        words = st["search_term"].lower().split()
        for i in range(len(words) - ngram_size + 1):
            ngram = " ".join(words[i:i + ngram_size])

            # Skip stop words, single chars, numbers
            if ngram in STOP_WORDS:
                continue
            if len(ngram) <= 1:
                continue
            if ngram.isdigit():
                continue

            data = ngram_data[ngram]
            data["impressions"] += st["impressions"]
            data["clicks"] += st["clicks"]
            data["cost"] += st["cost"]
            data["conversions"] += st["conversions"]
            data["search_terms"].add(st["search_term"])
            data["campaigns"].add((st["campaign_id"], st["campaign_name"]))

    # Filter to candidates: meet thresholds, no conversions
    candidates = []
    for ngram, data in ngram_data.items():
        if (data["impressions"] >= min_impressions
                and data["conversions"] <= max_conversions
                and data["cost"] >= min_spend):
            candidates.append({
                "ngram": ngram,
                "impressions": data["impressions"],
                "clicks": data["clicks"],
                "cost": round(data["cost"], 2),
                "conversions": data["conversions"],
                "search_term_count": len(data["search_terms"]),
                "sample_terms": list(data["search_terms"])[:5],
                "campaigns": [(cid, cname) for cid, cname in data["campaigns"]],
            })

    # Sort by cost descending (worst offenders first)
    candidates.sort(key=lambda x: x["cost"], reverse=True)
    return candidates


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------
def slack_post(token, channel, text, thread_ts=None):
    """Post a message to Slack."""
    payload = {
        "channel": channel,
        "text": text,
        "unfurl_links": False,
        "unfurl_media": False,
    }
    if thread_ts:
        payload["thread_ts"] = thread_ts

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result


def slack_get_replies(token, channel, thread_ts):
    """Get replies to a specific thread."""
    params = urllib.parse.urlencode({
        "channel": channel,
        "ts": thread_ts,
        "limit": 100,
    })
    req = urllib.request.Request(
        f"https://slack.com/api/conversations.replies?{params}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("messages", [])


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_mine(args):
    """Mine search terms, analyze n-grams, post candidates to Slack."""
    env = load_env()
    config = load_config()
    state = load_state()

    account_key = args.account or list(config["accounts"].keys())[0]
    account = config["accounts"][account_key]
    customer_id = account["customer_id"]
    label = account["label"]

    print(f"Connecting to Google Ads for {label} ({customer_id})...")
    client = get_google_ads_client(env, config)

    print(f"Fetching L{config['lookback_days']}D search terms...")
    search_terms = fetch_search_terms(client, customer_id, config["lookback_days"])
    print(f"  Found {len(search_terms)} search term entries")

    if not search_terms:
        print("No search terms found. Exiting.")
        return

    print("Fetching existing negative keywords...")
    existing_negatives = get_existing_negatives(client, customer_id)
    print(f"  Found {len(existing_negatives)} existing negatives")

    print("Running n-gram analysis...")
    candidates = analyze_ngrams(
        search_terms,
        ngram_size=config.get("ngram_size", 1),
        min_impressions=config.get("min_impressions", 10),
        max_conversions=config.get("max_conversions", 0),
        min_spend=config.get("min_spend", 0),
    )

    # Filter out terms that are already negatives or previously dismissed
    dismissed = set(state.get("dismissed", []))
    candidates = [c for c in candidates if c["ngram"] not in existing_negatives and c["ngram"] not in dismissed]
    print(f"  Found {len(candidates)} new candidates after filtering existing negatives and {len(dismissed)} dismissed")

    if not candidates:
        print("No new negative keyword candidates found.")
        return

    # Cap at top 20 to avoid Slack spam
    candidates = candidates[:20]

    # Post all candidates in a single message with numbered list
    slack_token = env["SLACK_XOXP_TOKEN"]
    channel = config["slack_channel"]

    # Build notify tag string from config
    notify_users = account.get("notify", [])
    notify_str = " ".join(f"<@{uid}>" for uid in notify_users)

    lines = [
        f":mag: *N-Gram Negative KW Report — {label}*",
        f"_L{config['lookback_days']}D | {len(search_terms)} search terms | {len(candidates)} candidates_",
        f"_Reply in thread: `approve 1,3,5` or `approve all` | `disapprove 2,4`_",
    ]
    if notify_str:
        lines.append(f"cc {notify_str}")
    lines.append("")

    candidate_map = {}
    for i, c in enumerate(candidates, 1):
        sample = ", ".join(c["sample_terms"][:3])
        campaign_names = ", ".join(set(cname for _, cname in c["campaigns"]))
        campaign_ids = [cid for cid, _ in c["campaigns"]]

        lines.append(
            f"*{i}.* `{c['ngram']}` — "
            f"{c['impressions']:,} imp | {c['clicks']:,} clicks | "
            f"${c['cost']:.2f} spend | {c['conversions']:.0f} conv"
        )
        lines.append(f"    _{sample}_")

        candidate_map[str(i)] = {
            "ngram": c["ngram"],
            "cost": c["cost"],
            "campaign_ids": campaign_ids,
            "campaigns": campaign_names,
            "status": "pending",
        }

    msg = "\n".join(lines)
    result = slack_post(slack_token, channel, msg)

    if result.get("ok"):
        thread_ts = result["ts"]
        state["last_run"] = datetime.now().isoformat()
        state["pending_approvals"] = {
            "thread_ts": thread_ts,
            "candidates": candidate_map,
            "posted_at": datetime.now().isoformat(),
        }
        save_state(state)
        print(f"Posted {len(candidate_map)} candidates to Slack (single thread)")
        print(json.dumps({"ok": True, "candidates": len(candidate_map)}, indent=2))
    else:
        print(f"Slack post failed: {result}", file=sys.stderr)


def parse_numbers(text):
    """Extract numbers from text like 'approve 1, 3, 5-7' or 'approve all'."""
    nums = set()
    for part in re.findall(r'[\d\-]+', text):
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                nums.update(range(int(start), int(end) + 1))
            except ValueError:
                pass
        else:
            try:
                nums.add(int(part))
            except ValueError:
                pass
    return nums


def cmd_check_approvals(args):
    """Check Slack thread for approve/disapprove replies and act on them."""
    env = load_env()
    config = load_config()
    state = load_state()

    account_key = args.account or list(config["accounts"].keys())[0]
    account = config["accounts"][account_key]
    customer_id = account["customer_id"]

    slack_token = env["SLACK_XOXP_TOKEN"]
    channel = config["slack_channel"]
    match_type = config.get("negative_kw_match_type", "EXACT")

    pending_data = state.get("pending_approvals", {})
    thread_ts = pending_data.get("thread_ts")
    candidates = pending_data.get("candidates", {})

    if not thread_ts or not candidates:
        print("No pending approvals found.")
        return

    # Check for pending items
    pending_nums = [k for k, v in candidates.items() if v["status"] == "pending"]
    if not pending_nums:
        print("All candidates already processed.")
        return

    # Get thread replies
    replies = slack_get_replies(slack_token, channel, thread_ts)

    approve_nums = set()
    disapprove_nums = set()

    for reply in replies[1:]:  # Skip original message
        text = reply.get("text", "").strip().lower()

        if text.startswith("approve") and not text.startswith("disapprove"):
            if "all" in text:
                approve_nums = set(int(k) for k in candidates.keys())
            else:
                approve_nums.update(parse_numbers(text))

        elif text.startswith("disapprove"):
            if "all" in text:
                disapprove_nums = set(int(k) for k in candidates.keys())
            else:
                disapprove_nums.update(parse_numbers(text))

    # Don't double-approve something disapproved in a later message
    approve_nums -= disapprove_nums

    client = None
    applied = []
    failed = []
    disapproved = []

    for num in sorted(approve_nums):
        key = str(num)
        if key not in candidates or candidates[key]["status"] != "pending":
            continue

        info = candidates[key]
        if client is None:
            client = get_google_ads_client(env, config)

        success = True
        for campaign_id in info["campaign_ids"]:
            try:
                apply_negative_keyword(client, customer_id, campaign_id, info["ngram"], match_type)
            except Exception as e:
                failed.append(f"{info['ngram']} (campaign {campaign_id}): {e}")
                success = False

        if success:
            info["status"] = "applied"
            info["applied_at"] = datetime.now().isoformat()
            applied.append(info["ngram"])
            state.setdefault("applied", []).append(info["ngram"])

    for num in sorted(disapprove_nums):
        key = str(num)
        if key not in candidates or candidates[key]["status"] != "pending":
            continue
        candidates[key]["status"] = "disapproved"
        disapproved.append(candidates[key]["ngram"])
        state.setdefault("dismissed", []).append(candidates[key]["ngram"])

    # Post summary back to thread
    summary_parts = []
    if applied:
        summary_parts.append(f":white_check_mark: *Applied {len(applied)} negatives:* {', '.join(f'`{k}`' for k in applied)}")
    if disapproved:
        summary_parts.append(f":no_entry_sign: *Skipped {len(disapproved)}:* {', '.join(f'`{k}`' for k in disapproved)}")
    if failed:
        summary_parts.append(f":warning: *Failed:* {'; '.join(failed)}")

    still_pending = sum(1 for v in candidates.values() if v["status"] == "pending")
    if still_pending:
        summary_parts.append(f"_{still_pending} still pending_")

    if summary_parts:
        slack_post(slack_token, channel, "\n".join(summary_parts), thread_ts=thread_ts)

    save_state(state)
    print(json.dumps({
        "applied": applied,
        "disapproved": disapproved,
        "failed": failed,
        "still_pending": still_pending,
    }, indent=2))


def cmd_apply(args):
    """Directly apply a single negative keyword."""
    env = load_env()
    config = load_config()

    account_key = args.account or list(config["accounts"].keys())[0]
    account = config["accounts"][account_key]
    customer_id = account["customer_id"]
    match_type = config.get("negative_kw_match_type", "EXACT")

    client = get_google_ads_client(env, config)
    result = apply_negative_keyword(client, customer_id, args.campaign_id, args.keyword, match_type)
    print(json.dumps({"ok": True, "resource": result}))


def cmd_watch(args):
    """Poll the Slack thread for replies, run check-approvals when 'done' is seen."""
    import time

    env = load_env()
    config = load_config()
    slack_token = env["SLACK_XOXP_TOKEN"]
    channel = config["slack_channel"]
    poll_interval = args.poll_interval or 30

    print(f"Watching for replies every {poll_interval}s. Ctrl+C to stop.")

    seen_replies = set()
    last_processed = None

    while True:
        state = load_state()
        pending_data = state.get("pending_approvals", {})
        thread_ts = pending_data.get("thread_ts")
        candidates = pending_data.get("candidates", {})

        if not thread_ts:
            print("No pending thread. Exiting watch.")
            break

        # Check if anything is still pending
        still_pending = sum(1 for v in candidates.values() if v["status"] == "pending")
        if still_pending == 0:
            print("All candidates processed. Exiting watch.")
            break

        replies = slack_get_replies(slack_token, channel, thread_ts)
        new_replies = [r for r in replies[1:] if r.get("ts") not in seen_replies]

        if new_replies:
            for r in new_replies:
                seen_replies.add(r["ts"])

            # Check if any reply contains approve/disapprove
            has_action = any(
                r.get("text", "").strip().lower().startswith(("approve", "disapprove"))
                for r in new_replies
            )

            if has_action:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Found approval reply, processing...")
                cmd_check_approvals(args)

                # Reload state to check if anything is left
                state = load_state()
                pending_data = state.get("pending_approvals", {})
                candidates = pending_data.get("candidates", {})
                still_pending = sum(1 for v in candidates.values() if v["status"] == "pending")
                if still_pending == 0:
                    print("All candidates processed. Exiting watch.")
                    break

        time.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="N-Gram Negative Keyword Miner")
    parser.add_argument("--mode", required=True, choices=["mine", "check-approvals", "apply", "watch"])
    parser.add_argument("--account", default=None, help="Account key from config.json")
    parser.add_argument("--keyword", default=None, help="Keyword to apply (for --mode apply)")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between polls (for --mode watch)")
    parser.add_argument("--campaign-id", default=None, help="Campaign ID (for --mode apply)")

    args = parser.parse_args()

    if args.mode == "mine":
        cmd_mine(args)
    elif args.mode == "check-approvals":
        cmd_check_approvals(args)
    elif args.mode == "watch":
        cmd_watch(args)
    elif args.mode == "apply":
        if not args.keyword or not args.campaign_id:
            parser.error("--keyword and --campaign-id required for apply mode")
        cmd_apply(args)


if __name__ == "__main__":
    main()
