#!/usr/bin/env python3
"""
Audience Auditor for Google Ads.

Pulls user_list (audience) resources from a Google Ads account via the
Google Ads API, matches them against the audience definitions in config.json,
and outputs a JSON gap report for Claude to interpret and present.

Usage:
  python audience_auditor.py --account barker-wellness
  python audience_auditor.py --account train-with-dave
"""

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
ENV_PATH = SCRIPT_DIR.parent.parent.parent / ".env"


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


def get_google_ads_client(env, config):
    from google.ads.googleads.client import GoogleAdsClient

    credentials_config = {
        "developer_token": env["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": env["GOOGLE_OAUTH_CLIENT_ID"],
        "client_secret": env["GOOGLE_OAUTH_CLIENT_SECRET"],
        "login_customer_id": config["mcc_id"],
        "use_proto_plus": True,
    }

    if "GOOGLE_ADS_REFRESH_TOKEN" in env:
        credentials_config["refresh_token"] = env["GOOGLE_ADS_REFRESH_TOKEN"]
    else:
        print("ERROR: No GOOGLE_ADS_REFRESH_TOKEN in .env.", file=sys.stderr)
        sys.exit(1)

    return GoogleAdsClient.load_from_dict(credentials_config)


def fetch_user_lists(client, customer_id):
    """Fetch all user lists (audiences) for the account, excluding Similar lists."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            user_list.id,
            user_list.name,
            user_list.description,
            user_list.type,
            user_list.size_for_search,
            user_list.size_for_display,
            user_list.membership_life_span,
            user_list.membership_status
        FROM user_list
        WHERE user_list.membership_status = 'OPEN'
        ORDER BY user_list.name
    """

    results = []
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in response:
        for row in batch.results:
            ul = row.user_list
            # Skip "Similar to ..." lists — auto-generated, not real audiences
            if ul.name.lower().startswith("similar to "):
                continue
            results.append({
                "id": ul.id,
                "name": ul.name,
                "description": ul.description or "",
                "type": ul.type_.name if hasattr(ul.type_, 'name') else str(ul.type_),
                "size_search": ul.size_for_search,
                "size_display": ul.size_for_display,
                "membership_days": ul.membership_life_span,
                "status": ul.membership_status.name if hasattr(ul.membership_status, 'name') else str(ul.membership_status),
            })

    return results


def fetch_remarketing_actions(client, customer_id):
    """Fetch remarketing actions (pixel/tag based) for the account."""
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            remarketing_action.id,
            remarketing_action.name
        FROM remarketing_action
    """

    results = []
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in response:
            for row in batch.results:
                ra = row.remarketing_action
                results.append({
                    "id": ra.id,
                    "name": ra.name,
                })
    except Exception:
        # Some accounts may not have remarketing actions
        pass

    return results


# Negation phrases that invert the meaning of a keyword match.
# e.g. "Did Not Purchase" should NOT match the "Purchasers" definition.
NEGATION_PHRASES = [
    "did not ", "non-", "non ", "not ", "without ", "never ",
    "excluding ", "exclude ",
]


def match_audience(user_list_name, definition):
    """Check if a user list name matches an audience definition's keywords.

    Returns False if the list name contains a negation phrase immediately
    before or surrounding the matched keyword (e.g. "Did Not Purchase").
    """
    name_lower = user_list_name.lower()
    for keyword in definition["match_keywords"]:
        kw = keyword.lower()
        pos = name_lower.find(kw)
        if pos == -1:
            continue
        # Check whether a negation phrase appears before the keyword
        prefix = name_lower[:pos]
        if any(prefix.rstrip().endswith(neg.rstrip()) or prefix.endswith(neg)
               for neg in NEGATION_PHRASES):
            continue  # negated — skip this keyword
        return True
    return False


def audit_account(user_lists, audience_definitions, account_type):
    """Match existing user lists against defined audiences, find gaps."""
    definitions = audience_definitions.get(account_type, [])

    matched = []
    gaps = []

    for defn in definitions:
        matching_lists = []
        for ul in user_lists:
            if match_audience(ul["name"], defn):
                matching_lists.append(ul)

        if matching_lists:
            matched.append({
                "definition": defn,
                "existing_lists": matching_lists,
            })
        else:
            gaps.append(defn)

    # Find unmatched user lists (exist in account but not in our checklist)
    matched_list_ids = set()
    for m in matched:
        for ul in m["existing_lists"]:
            matched_list_ids.add(ul["id"])

    unmatched_lists = [ul for ul in user_lists if ul["id"] not in matched_list_ids]

    return {
        "matched": matched,
        "gaps": gaps,
        "unmatched_lists": unmatched_lists,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Google Ads audience coverage")
    parser.add_argument("--account", required=True, help="Account key from config.json")
    args = parser.parse_args()

    config = load_config()
    env = load_env()

    if args.account not in config["accounts"]:
        valid = ", ".join(config["accounts"].keys())
        print(json.dumps({
            "error": f"Unknown account '{args.account}'. Valid: {valid}"
        }))
        sys.exit(1)

    account = config["accounts"][args.account]
    customer_id = account["customer_id"]
    account_type = account["type"]

    client = get_google_ads_client(env, config)

    user_lists = fetch_user_lists(client, customer_id)
    remarketing_actions = fetch_remarketing_actions(client, customer_id)

    audit = audit_account(user_lists, config["audience_definitions"], account_type)

    # Build summary stats
    definitions = config["audience_definitions"].get(account_type, [])
    total_defined = len(definitions)
    total_matched = len(audit["matched"])
    total_gaps = len(audit["gaps"])

    critical_gaps = [g for g in audit["gaps"] if g.get("priority") == "critical"]
    high_gaps = [g for g in audit["gaps"] if g.get("priority") == "high"]
    medium_gaps = [g for g in audit["gaps"] if g.get("priority") == "medium"]
    low_gaps = [g for g in audit["gaps"] if g.get("priority") == "low"]

    coverage_pct = round((total_matched / total_defined * 100), 1) if total_defined > 0 else 0

    output = {
        "account": args.account,
        "label": account["label"],
        "customer_id": customer_id,
        "account_type": account_type,
        "platform": account.get("platform", "unknown"),
        "summary": {
            "total_defined": total_defined,
            "total_matched": total_matched,
            "total_gaps": total_gaps,
            "coverage_pct": coverage_pct,
            "critical_gaps": len(critical_gaps),
            "high_gaps": len(high_gaps),
            "medium_gaps": len(medium_gaps),
            "low_gaps": len(low_gaps),
        },
        "matched": [
            {
                "id": m["definition"]["id"],
                "name": m["definition"]["name"],
                "priority": m["definition"].get("priority", "medium"),
                "existing_lists": [
                    {"name": ul["name"], "size_search": ul["size_search"], "size_display": ul["size_display"]}
                    for ul in m["existing_lists"]
                ],
            }
            for m in audit["matched"]
        ],
        "gaps": [
            {
                "id": g["id"],
                "name": g["name"],
                "priority": g.get("priority", "medium"),
                "description": g.get("description", ""),
                "build_method": g.get("build_method", ""),
                "alt_method": g.get("alt_method"),
            }
            for g in audit["gaps"]
        ],
        "unmatched_lists": audit["unmatched_lists"],
        "remarketing_actions": remarketing_actions,
        "total_user_lists": len(user_lists),
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
