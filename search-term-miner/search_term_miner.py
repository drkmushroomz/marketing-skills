#!/usr/bin/env python3
"""Search Term Miner — find, score, and promote converting search terms.

Pulls search terms from the last N days, finds ones with conversions,
checks if they already exist as keywords, scores each for quality vs
random luck, and optionally adds the strong ones.

Usage:
    python search_term_miner.py                            # Suggest mode (all accounts)
    python search_term_miner.py --account train-with-dave  # One account
    python search_term_miner.py --add                      # Add 'strong' terms (live)
    python search_term_miner.py --add --include-review      # Also add 'review' terms
    python search_term_miner.py --dry-run                  # Legacy: same as suggest
    python search_term_miner.py --lookback 14              # Override lookback window
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


# ---------------------------------------------------------------------------
# Config / state helpers
# ---------------------------------------------------------------------------

def load_config():
    return json.loads(CONFIG_PATH.read_text())


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"last_run": {}, "added": {}}


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Google Ads data fetching
# ---------------------------------------------------------------------------

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
        # Keys come back camelCase from MessageToDict
        stv = row.get("searchTermView", row.get("search_term_view", {}))
        campaign = row.get("campaign", {})
        ad_group = row.get("adGroup", row.get("ad_group", {}))
        metrics = row.get("metrics", {})

        terms.append({
            "search_term": stv.get("searchTerm", stv.get("search_term", "")),
            "campaign_id": str(campaign.get("id", "")),
            "campaign_name": campaign.get("name", ""),
            "ad_group_id": str(ad_group.get("id", "")),
            "ad_group_name": ad_group.get("name", ""),
            "impressions": int(metrics.get("impressions", 0)),
            "clicks": int(metrics.get("clicks", 0)),
            "cost": int(metrics.get("costMicros", metrics.get("cost_micros", 0))) / 1_000_000,
            "conversions": float(metrics.get("conversions", 0)),
            "conversion_value": float(metrics.get("conversionsValue", metrics.get("conversions_value", 0))),
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
        agc = row.get("adGroupCriterion", row.get("ad_group_criterion", {}))
        kw = agc.get("keyword", {})
        text = kw.get("text", "").lower()
        match_type = kw.get("matchType", kw.get("match_type", ""))
        if isinstance(match_type, int):
            mt_map = {0: "UNSPECIFIED", 1: "UNKNOWN", 2: "EXACT", 3: "PHRASE", 4: "BROAD"}
            match_type = mt_map.get(match_type, str(match_type))
        keywords.add((text, match_type))
    return keywords


def fetch_existing_keyword_texts(customer_id):
    """Get just the keyword texts (lowered) for semantic comparison."""
    query = """
        SELECT
            ad_group_criterion.keyword.text
        FROM ad_group_criterion
        WHERE ad_group_criterion.type = 'KEYWORD'
            AND ad_group_criterion.status != 'REMOVED'
            AND campaign.status = 'ENABLED'
    """
    rows = run_gaql(customer_id, query)
    texts = set()
    for row in rows:
        agc = row.get("adGroupCriterion", row.get("ad_group_criterion", {}))
        kw = agc.get("keyword", {})
        text = kw.get("text", "").lower().strip()
        if text:
            texts.add(text)
    return texts


def fetch_account_avg_cpa(customer_id, lookback_days):
    """Get account-level average CPA for the lookback window."""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    query = f"""
        SELECT
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status = 'ENABLED'
            AND metrics.conversions > 0
    """
    rows = run_gaql(customer_id, query)
    total_cost = 0
    total_conv = 0
    for row in rows:
        m = row.get("metrics", {})
        total_cost += int(m.get("costMicros", m.get("cost_micros", 0)))
        total_conv += float(m.get("conversions", 0))

    if total_conv > 0:
        return (total_cost / 1_000_000) / total_conv
    return None


# ---------------------------------------------------------------------------
# Keyword quality scoring
# ---------------------------------------------------------------------------

def _word_overlap(search_term, keyword_texts):
    """What fraction of the search term's words appear in existing keywords."""
    st_words = set(search_term.lower().split())
    # Build a set of all words across existing keywords
    kw_words = set()
    for kw in keyword_texts:
        kw_words.update(kw.split())

    if not st_words:
        return 0.0
    overlap = st_words & kw_words
    return len(overlap) / len(st_words)


LOCAL_INTENT_PATTERNS = (
    "near me", "close to me", "in my area", "nearby",
    "closest", "local", "around me",
)


def score_term(term, account_avg_cpa, keyword_texts, strong_threshold=None, geotargeted=False):
    """Score a converting search term for quality.

    Returns dict with score (0-100), classification, and reasons.
    Classification:
        strong  — high confidence, safe to auto-add
        review  — plausible but needs human judgement
        skip    — likely noise or bad fit

    strong_threshold: if set, any term with >= this many conversions is
        automatically classified as 'strong' (for low-volume accounts
        where 2-3 conversions is already a clear signal).
    """
    score = 0
    reasons = []

    conversions = term["conversions"]
    clicks = term["clicks"]
    impressions = term["impressions"]
    cost = term["cost"]
    cpa = cost / conversions if conversions else float("inf")
    cvr = conversions / clicks if clicks else 0
    ctr = clicks / impressions if impressions else 0
    words = term["search_term"].split()
    word_count = len(words)

    # --- Conversion volume (more = more statistically reliable) ---
    if conversions >= 5:
        score += 30
        reasons.append(f"{conversions:.0f} conversions (high confidence)")
    elif conversions >= 3:
        score += 22
        reasons.append(f"{conversions:.0f} conversions (good signal)")
    elif conversions >= 2:
        score += 12
        reasons.append(f"{conversions:.0f} conversions (moderate signal)")
    else:
        score += 4
        reasons.append("1 conversion (weak signal)")

    # --- Conversion rate ---
    if cvr >= 0.15:
        score += 20
        reasons.append(f"CVR {cvr:.0%} (excellent)")
    elif cvr >= 0.08:
        score += 14
        reasons.append(f"CVR {cvr:.0%} (strong)")
    elif cvr >= 0.04:
        score += 8
        reasons.append(f"CVR {cvr:.0%} (decent)")
    elif clicks >= 3:
        score += 2
        reasons.append(f"CVR {cvr:.0%} (low)")

    # --- CPA vs account average ---
    if account_avg_cpa:
        if cpa <= account_avg_cpa * 0.7:
            score += 20
            reasons.append(f"CPA ${cpa:.2f} well below avg ${account_avg_cpa:.2f}")
        elif cpa <= account_avg_cpa:
            score += 14
            reasons.append(f"CPA ${cpa:.2f} below avg ${account_avg_cpa:.2f}")
        elif cpa <= account_avg_cpa * 1.5:
            score += 6
            reasons.append(f"CPA ${cpa:.2f} within 1.5x avg ${account_avg_cpa:.2f}")
        else:
            score -= 5
            reasons.append(f"CPA ${cpa:.2f} exceeds 1.5x avg ${account_avg_cpa:.2f}")

    # --- Click volume (statistical confidence) ---
    if clicks >= 20:
        score += 10
        reasons.append(f"{clicks} clicks (solid data)")
    elif clicks >= 10:
        score += 7
    elif clicks >= 5:
        score += 4
    elif clicks < 3:
        score -= 3
        reasons.append(f"only {clicks} clicks (thin data)")

    # --- CTR (intent signal) ---
    if ctr >= 0.08:
        score += 5
        reasons.append(f"CTR {ctr:.1%} (high intent)")
    elif ctr < 0.02 and impressions >= 50:
        score -= 3
        reasons.append(f"CTR {ctr:.1%} (low relevance signal)")

    # --- Query structure ---
    if word_count >= 7:
        score -= 8
        reasons.append(f"{word_count}-word query (ultra long-tail, unlikely to scale)")
    elif word_count >= 5:
        score -= 3
        reasons.append(f"{word_count}-word query (long-tail)")
    elif word_count == 1:
        score -= 5
        reasons.append("single word (too broad, likely expensive)")
    elif word_count in (2, 3):
        score += 3  # sweet spot

    # --- Local intent (high-value when account is geotargeted) ---
    st_lower = term["search_term"].lower()
    has_local_intent = any(p in st_lower for p in LOCAL_INTENT_PATTERNS)
    if has_local_intent:
        if geotargeted:
            score += 12
            reasons.append("local-intent query + geotargeted account (strong fit)")
        else:
            score += 3
            reasons.append("local-intent query (no geotargeting confirmed)")

    # --- Semantic relevance to existing keywords ---
    overlap = _word_overlap(term["search_term"], keyword_texts)
    if overlap >= 0.8:
        score += 10
        reasons.append("high word overlap with existing keywords (on-theme)")
    elif overlap >= 0.5:
        score += 5
        reasons.append("moderate word overlap with existing keywords")
    elif overlap < 0.2 and word_count >= 2:
        score -= 8
        reasons.append("low word overlap (off-theme — may be random luck)")

    # --- Clamp score ---
    score = max(0, min(100, score))

    # --- Classify ---
    if strong_threshold and conversions >= strong_threshold:
        # Low-volume account override: hitting the conversion threshold
        # is enough signal regardless of other factors
        classification = "strong"
        score = max(score, 55)
        reasons.insert(0, f"{conversions:.0f}+ conv (meets account threshold of {strong_threshold})")
    elif score >= 55:
        classification = "strong"
    elif score >= 30:
        classification = "review"
    else:
        classification = "skip"

    return {
        "score": score,
        "classification": classification,
        "reasons": reasons,
        "cpa": cpa,
        "cvr": cvr,
        "ctr": ctr,
    }


# ---------------------------------------------------------------------------
# Gap analysis
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Keyword addition
# ---------------------------------------------------------------------------

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
                "classification": gap.get("classification", "unknown"),
                "quality_score": gap.get("quality_score", 0),
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
                criterion.keyword.match_type = getattr(
                    client.enums.KeywordMatchTypeEnum, match_type
                )
                criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED  # =2
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


# ---------------------------------------------------------------------------
# Slack notifications
# ---------------------------------------------------------------------------

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

    if channel:
        _slack_post(token, channel, text)

    if dm_user_ids:
        for user_id in dm_user_ids:
            _slack_post(token, user_id, text)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

EMOJI_MAP = {"strong": ":white_check_mark:", "review": ":eyes:", "skip": ":no_entry_sign:"}
LABEL_MAP = {"strong": "STRONG", "review": "REVIEW", "skip": "SKIP"}


def format_scored_report(label, scored_gaps, results, mode, account_avg_cpa):
    """Format a summary with quality scores."""
    lines = []

    if mode == "add":
        lines.append(f":rocket: *Search Term Miner: {label}* — keywords added")
    else:
        lines.append(f":mag: *Search Term Miner: {label}* — suggestions")

    if account_avg_cpa:
        lines.append(f"Account avg CPA: ${account_avg_cpa:.2f}")

    if not scored_gaps:
        lines.append("No new converting search terms found.")
        return "\n".join(lines)

    # Group by classification
    by_class = {"strong": [], "review": [], "skip": []}
    for g in scored_gaps:
        by_class[g["classification"]].append(g)

    for cls in ("strong", "review", "skip"):
        items = by_class[cls]
        if not items:
            continue

        emoji = EMOJI_MAP[cls]
        lines.append(f"\n{emoji} *{LABEL_MAP[cls]}* ({len(items)})")

        for g in items:
            conv = g["conversions"]
            cost = g["cost"]
            cpa = g.get("cpa", cost / conv if conv else 0)
            cvr = g.get("cvr", 0)
            score = g.get("quality_score", 0)
            types = []
            if g["needs_exact"]:
                types.append("EXACT")
            if g["needs_broad"]:
                types.append("BROAD")

            lines.append(
                f"  `{g['search_term']}`"
                f"  |  score: {score}"
                f"  |  {conv:.0f} conv  |  CVR {cvr:.0%}"
                f"  |  ${cpa:.2f} CPA"
                f"  |  +{', '.join(types)}"
                f"  |  _{g['ad_group_name']}_"
            )

            # Top reasons (keep it concise for Slack)
            top_reasons = g.get("reasons", [])[:3]
            if top_reasons:
                lines.append(f"    _{'  ·  '.join(top_reasons)}_")

    # Addition results
    if results:
        added = results.get("added", [])
        errors = results.get("errors", [])
        if added:
            lines.append(f"\n*Keywords added: {len(added)}*")
        if errors:
            lines.append(f":warning: Errors: {len(errors)}")
            for e in errors:
                lines.append(f"  `{e['keyword']}` ({e['match_type']}): {e['error']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main pipeline per account
# ---------------------------------------------------------------------------

def run_account(account_key, account_config, global_config, mode="suggest", include_review=False):
    """Run the miner for a single account.

    mode: 'suggest' (score + report only) or 'add' (add strong terms)
    """
    customer_id = account_config["customer_id"]
    label = account_config.get("label", account_key)
    default_ag = account_config.get("default_ad_group_id")
    exact_bid = account_config.get("exact_bid", 1.50)
    broad_bid = account_config.get("broad_bid", 0.75)
    strong_threshold = account_config.get("strong_threshold")
    geotargeted = account_config.get("geotargeted", False)
    lookback = global_config.get("lookback_days", 7)
    min_conv = global_config.get("min_conversions", 1)

    print(f"\n--- {label} ({customer_id}) ---")
    print(f"Lookback: {lookback}d | Min conversions: {min_conv} | Mode: {mode}")
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

    # Step 4: Score each gap
    print("Scoring search term quality...")
    keyword_texts = fetch_existing_keyword_texts(customer_id)
    account_avg_cpa = fetch_account_avg_cpa(customer_id, lookback)
    if account_avg_cpa:
        print(f"  Account avg CPA: ${account_avg_cpa:.2f}")

    scored_gaps = []
    for gap in gaps:
        result = score_term(gap, account_avg_cpa, keyword_texts, strong_threshold, geotargeted)
        gap["quality_score"] = result["score"]
        gap["classification"] = result["classification"]
        gap["reasons"] = result["reasons"]
        gap["cpa"] = result["cpa"]
        gap["cvr"] = result["cvr"]
        gap["ctr"] = result["ctr"]
        scored_gaps.append(gap)

    # Sort by score descending
    scored_gaps.sort(key=lambda g: g["quality_score"], reverse=True)

    counts = {"strong": 0, "review": 0, "skip": 0}
    for g in scored_gaps:
        counts[g["classification"]] += 1
    print(f"  Scored: {counts['strong']} strong, {counts['review']} review, {counts['skip']} skip")

    # Step 5: Add keywords if in add mode
    results = None
    if mode == "add":
        to_add = [g for g in scored_gaps if g["classification"] == "strong"]
        if include_review:
            to_add.extend(g for g in scored_gaps if g["classification"] == "review")

        if to_add:
            print(f"Adding {len(to_add)} keywords (LIVE)...")
            results = add_keywords_to_account(
                customer_id, default_ag, to_add, exact_bid, broad_bid, dry_run=False
            )
        else:
            print("  No terms qualified for auto-add.")

    report = format_scored_report(label, scored_gaps, results, mode, account_avg_cpa)
    print(f"\n{report}")

    return report, scored_gaps


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Search Term Miner")
    parser.add_argument("--account", help="Run for a specific account alias")
    parser.add_argument("--add", action="store_true",
                        help="Add 'strong' terms to the account (default: suggest only)")
    parser.add_argument("--include-review", action="store_true",
                        help="When --add, also add 'review' terms")
    parser.add_argument("--lookback", type=int, help="Override lookback days")
    parser.add_argument("--dry-run", action="store_true",
                        help="Legacy flag — equivalent to suggest mode (no --add)")
    args = parser.parse_args()

    config = load_config()
    state = load_state()

    # Determine mode
    if args.add and not args.dry_run:
        mode = "add"
    else:
        mode = "suggest"

    # Override lookback if specified
    if args.lookback:
        config["lookback_days"] = args.lookback

    # Ensure env vars are set
    env_file = PROJECT_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val

    # Set MCC login customer ID from config
    mcc_id = config.get("mcc_id")
    if mcc_id:
        os.environ.setdefault("GOOGLE_ADS_LOGIN_CUSTOMER_ID", str(mcc_id).replace("-", ""))

    accounts = config["accounts"]
    if args.account:
        if args.account not in accounts:
            print(f"Unknown account: {args.account}")
            print(f"Available: {', '.join(accounts.keys())}")
            sys.exit(1)
        accounts = {args.account: accounts[args.account]}

    all_reports = []

    for key, acct in accounts.items():
        report, scored_gaps = run_account(key, acct, config, mode, args.include_review)

        if report:
            all_reports.append(report)
            state["last_run"][key] = datetime.now().isoformat()

            if mode == "add" and scored_gaps:
                if key not in state["added"]:
                    state["added"][key] = []
                for g in scored_gaps:
                    if g["classification"] == "strong" or (
                        args.include_review and g["classification"] == "review"
                    ):
                        state["added"][key].append({
                            "term": g["search_term"],
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "conversions": g["conversions"],
                            "score": g["quality_score"],
                            "classification": g["classification"],
                        })

    save_state(state)

    # Slack notification — always notify (suggest mode = suggestions, add mode = additions)
    slack_channel = config.get("slack_channel")
    dm_config = config.get("slack_dm", {})
    if all_reports:
        full_report = "\n\n".join(all_reports)

        dm_users = []
        for key in accounts:
            dm_users.extend(dm_config.get(key, []))

        slack_notify(slack_channel, full_report, dm_user_ids=dm_users or None)


if __name__ == "__main__":
    main()
