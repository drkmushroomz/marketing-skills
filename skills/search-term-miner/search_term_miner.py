#!/usr/bin/env python3
"""Search Term Miner — auto-promote converting search terms to keywords.

Pulls search terms from the last N days, finds ones with conversions,
checks if they already exist as keywords, and adds missing ones with
both exact and broad match types at staggered bids.

Usage:
    python search_term_miner.py                            # All configured accounts
    python search_term_miner.py --account train-with-dave  # One account
    python search_term_miner.py --dry-run                  # Preview only
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR / "mcp-servers" / "google-ads"))

from gads_client import make_client, run_gaql, dollars_to_micros  # noqa: E402

CONFIG_PATH = SCRIPT_DIR / "config.json"
STATE_PATH = SCRIPT_DIR / "state.json"


def load_config():
    return json.loads(CONFIG_PATH.read_text())


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_run": {}, "added": {}}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def fetch_converting_search_terms(customer_id, lookback_days, min_conversions):
    """Pull search terms with conversions in the lookback window."""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    query = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value
        FROM search_term_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND metrics.conversions > {min_conversions - 1.0}
            AND campaign.status = 'ENABLED'
        ORDER BY metrics.conversions DESC
        LIMIT 1000
    """

    rows = run_gaql(customer_id, query)
    terms = []
    for row in rows:
        stv = row.get("search_term_view", {})
        campaign = row.get("campaign", {})
        ad_group = row.get("ad_group", {})
        metrics = row.get("metrics", {})

        terms.append({
            "search_term": stv.get("search_term", ""),
            "campaign_id": str(campaign.get("id", "")),
            "campaign_name": campaign.get("name", ""),
            "ad_group_id": str(ad_group.get("id", "")),
            "ad_group_name": ad_group.get("name", ""),
            "impressions": int(metrics.get("impressions", 0)),
            "clicks": int(metrics.get("clicks", 0)),
            "cost": int(metrics.get("cost_micros", 0)) / 1_000_000,
            "conversions": float(metrics.get("conversions", 0)),
            "conversion_value": float(metrics.get("conversions_value", 0)),
        })
    return terms


def fetch_existing_keywords(customer_id):
    """Get all active keywords in the account for dedup."""
    query = """
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type
        FROM ad_group_criterion
        WHERE ad_group_criterion.type = 'KEYWORD'
            AND ad_group_criterion.status != 'REMOVED'
            AND campaign.status = 'ENABLED'
    """

    rows = run_gaql(customer_id, query)
    keywords = set()
    for row in rows:
        agc = row.get("ad_group_criterion", {})
        kw = agc.get("keyword", {})
        text = kw.get("text", "").lower()
        match_type = kw.get("match_type", "")
        # match_type comes back as int enum or string
        if isinstance(match_type, int):
            mt_map = {0: "UNSPECIFIED", 1: "UNKNOWN", 2: "EXACT", 3: "PHRASE", 4: "BROAD"}
            match_type = mt_map.get(match_type, str(match_type))
        keywords.add((text, match_type))
    return keywords


def find_gaps(converting_terms, existing_keywords):
    """Find converting search terms missing as keywords."""
    gaps = []
    seen = set()

    for term in converting_terms:
        st = term["search_term"].lower().strip()
        if st in seen:
            continue
        seen.add(st)

        has_exact = (st, "EXACT") in existing_keywords
        has_broad = (st, "BROAD") in existing_keywords

        if not has_exact or not has_broad:
            gaps.append({
                **term,
                "needs_exact": not has_exact,
                "needs_broad": not has_broad,
            })

    return gaps


def add_keywords_to_account(customer_id, ad_group_id, gaps, exact_bid, broad_bid, dry_run=False):
    """Add missing keywords with exact + broad at staggered bids."""
    client = make_client()
    ag_criterion_service = client.get_service("AdGroupCriterionService")
    ag_service = client.get_service("AdGroupService")

    results = {"added": [], "errors": []}

    for gap in gaps:
        text = gap["search_term"].lower().strip()
        target_ag = gap.get("ad_group_id", ad_group_id)

        to_add = []
        if gap["needs_exact"]:
            to_add.append(("EXACT", exact_bid))
        if gap["needs_broad"]:
            to_add.append(("BROAD", broad_bid))

        for match_type, bid in to_add:
            entry = {
                "keyword": text,
                "match_type": match_type,
                "bid": bid,
                "ad_group_id": target_ag,
                "ad_group_name": gap["ad_group_name"],
                "conversions": gap["conversions"],
                "cost": gap["cost"],
            }

            if dry_run:
                entry["dry_run"] = True
                results["added"].append(entry)
                continue

            try:
                op = client.get_type("AdGroupCriterionOperation")
                criterion = op.create
                criterion.ad_group = ag_service.ad_group_path(customer_id, target_ag)
                criterion.keyword.text = text
                criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[match_type].value
                criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                criterion.cpc_bid_micros = dollars_to_micros(bid)

                ag_criterion_service.mutate_ad_group_criteria(
                    customer_id=customer_id, operations=[op]
                )
                results["added"].append(entry)

            except Exception as e:
                results["errors"].append({
                    "keyword": text,
                    "match_type": match_type,
                    "error": str(e),
                })

    return results


def _get_slack_token():
    """Read Slack token from .env."""
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("SLACK_XOXP_TOKEN="):
                return line.split("=", 1)[1]
    return ""


def _slack_post(token, channel, text):
    """Post a message to a Slack channel or DM."""
    payload = json.dumps({"channel": channel, "text": text}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def slack_notify(channel, text, dm_user_ids=None):
    """Post results to Slack channel and optionally DM specific users."""
    token = _get_slack_token()
    if not token:
        return

    # Post to channel
    if channel:
        _slack_post(token, channel, text)

    # DM individual users
    if dm_user_ids:
        for user_id in dm_user_ids:
            _slack_post(token, user_id, text)


def format_report(label, gaps, results, dry_run):
    """Format a summary report."""
    lines = []
    mode = ":test_tube: [DRY RUN] " if dry_run else ":rocket: "
    lines.append(f"{mode}*Search Term Miner: {label}*")

    if not gaps:
        lines.append("No new converting search terms found.")
        return "\n".join(lines)

    lines.append(f"Converting search terms not yet keywords: *{len(gaps)}*\n")

    for g in gaps:
        conv = g["conversions"]
        cost = g["cost"]
        cpa = cost / conv if conv else 0
        types = []
        if g["needs_exact"]:
            types.append("EXACT")
        if g["needs_broad"]:
            types.append("BROAD")
        lines.append(
            f"  `{g['search_term']}`"
            f"  |  {conv:.0f} conv  |  ${cost:.2f}  |  ${cpa:.2f} CPA"
            f"  |  +{', '.join(types)}"
            f"  |  _{g['ad_group_name']}_"
        )

    added = results.get("added", [])
    errors = results.get("errors", [])

    lines.append(f"\n*Keywords added: {len(added)}*")
    if errors:
        lines.append(f":warning: Errors: {len(errors)}")
        for e in errors:
            lines.append(f"  `{e['keyword']}` ({e['match_type']}): {e['error']}")

    return "\n".join(lines)


def run_account(account_key, account_config, global_config, dry_run=False):
    """Run the miner for a single account."""
    customer_id = account_config["customer_id"]
    label = account_config.get("label", account_key)
    default_ag = account_config.get("default_ad_group_id")
    exact_bid = account_config.get("exact_bid", 1.50)
    broad_bid = account_config.get("broad_bid", 0.75)
    lookback = global_config.get("lookback_days", 7)
    min_conv = global_config.get("min_conversions", 1)

    print(f"\n--- {label} ({customer_id}) ---")
    print(f"Lookback: {lookback}d | Min conversions: {min_conv}")
    print(f"Bids: exact=${exact_bid:.2f} / broad=${broad_bid:.2f}")

    # Step 1: Fetch converting search terms
    print("Fetching converting search terms...")
    converting = fetch_converting_search_terms(customer_id, lookback, min_conv)
    print(f"  Found {len(converting)} converting search terms")

    if not converting:
        return None, []

    # Step 2: Fetch existing keywords
    print("Fetching existing keywords...")
    existing = fetch_existing_keywords(customer_id)
    print(f"  {len(existing)} keyword+match combos in account")

    # Step 3: Find gaps
    gaps = find_gaps(converting, existing)
    print(f"  {len(gaps)} search terms need keywords added")

    if not gaps:
        print("  All converting terms already covered.")
        return None, []

    # Step 4: Add keywords
    print(f"Adding keywords ({'DRY RUN' if dry_run else 'LIVE'})...")
    results = add_keywords_to_account(
        customer_id, default_ag, gaps, exact_bid, broad_bid, dry_run
    )

    report = format_report(label, gaps, results, dry_run)
    print(f"\n{report}")

    return report, gaps


def main():
    parser = argparse.ArgumentParser(description="Search Term Miner")
    parser.add_argument("--account", help="Run for a specific account alias")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    args = parser.parse_args()

    config = load_config()
    state = load_state()
    dry_run = args.dry_run or config.get("dry_run", False)

    # Ensure env vars are set (read from .env if needed)
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val

    accounts = config["accounts"]
    if args.account:
        if args.account not in accounts:
            print(f"Unknown account: {args.account}")
            print(f"Available: {', '.join(accounts.keys())}")
            sys.exit(1)
        accounts = {args.account: accounts[args.account]}

    all_reports = []

    for key, acct in accounts.items():
        report, gaps = run_account(key, acct, config, dry_run)

        if report:
            all_reports.append(report)
            state["last_run"][key] = datetime.now().isoformat()
            if not dry_run and gaps:
                if key not in state["added"]:
                    state["added"][key] = []
                for g in gaps:
                    state["added"][key].append({
                        "term": g["search_term"],
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "conversions": g["conversions"],
                    })

    save_state(state)

    # Slack notification
    slack_channel = config.get("slack_channel")
    dm_config = config.get("slack_dm", {})
    if all_reports and not dry_run:
        full_report = "\n\n".join(all_reports)

        # Collect DM user IDs for the accounts that ran
        dm_users = []
        for key in accounts:
            dm_users.extend(dm_config.get(key, []))

        slack_notify(slack_channel, full_report, dm_user_ids=dm_users or None)


if __name__ == "__main__":
    main()
