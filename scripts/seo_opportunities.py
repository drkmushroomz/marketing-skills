"""
SEO Opportunities Analyzer for jetfuel.agency
Pulls GSC data, identifies ranking opportunities, content gaps, and quick wins.
Outputs JSON for the Claude skill to write to Google Sheets.
"""
import json
import sys
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- Config ---
CONFIG_PATH = ".claude/ops/seo-opportunities/config.json"

with open(CONFIG_PATH) as f:
    config = json.load(f)

with open(config["oauth"]["tokens_file"]) as f:
    tokens = json.load(f)

CLIENT_ID = config["oauth"]["client_id"]
CLIENT_SECRET = config["oauth"]["client_secret"]
SITE_URL = config["gsc_property"]
LOOKBACK = config["lookback_days"]

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=LOOKBACK)).strftime("%Y-%m-%d")

creds = Credentials(
    token=tokens.get("access_token"),
    refresh_token=tokens["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
)

service = build("searchconsole", "v1", credentials=creds)


def pull_gsc(dimensions, row_limit=5000, filters=None):
    """Pull GSC data with pagination."""
    all_rows = []
    start_row = 0
    while True:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": min(row_limit, 1000),
            "startRow": start_row,
        }
        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]
        resp = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
        rows = resp.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        start_row += len(rows)
        if len(rows) < 1000 or start_row >= row_limit:
            break
    return all_rows


# --- Step 1: Pull all query data ---
print("Pulling GSC query data...", file=sys.stderr)
all_queries = pull_gsc(["query"], 5000)
print(f"  {len(all_queries)} queries", file=sys.stderr)

# --- Step 2: Pull page data ---
print("Pulling GSC page data...", file=sys.stderr)
all_pages = pull_gsc(["page"], 500)
print(f"  {len(all_pages)} pages", file=sys.stderr)

# --- Step 3: Pull niche-specific query×page data ---
niche_data = {}
for niche_key, niche_cfg in config["target_niches"].items():
    label = niche_cfg["label"]
    # Extract key terms from seed keywords for filtering
    niche_terms = set()
    for seed in niche_cfg["seed_keywords"]:
        for word in seed.lower().split():
            if word not in ("agency", "marketing", "digital", "brand", "ecommerce", "for", "and", "the", "a", "an", "in", "of"):
                niche_terms.add(word)

    # Filter queries matching this niche
    matching = []
    for row in all_queries:
        q = row["keys"][0].lower()
        if any(term in q for term in niche_terms):
            matching.append(row)

    niche_data[niche_key] = {
        "label": label,
        "terms": list(niche_terms),
        "matching_queries": len(matching),
        "queries": matching,
    }
    print(f"  {label}: {len(matching)} matching queries", file=sys.stderr)

# --- Build page index ---
existing_pages = {}
for row in all_pages:
    url = row["keys"][0]
    existing_pages[url] = {
        "clicks": row["clicks"],
        "impressions": row["impressions"],
        "ctr": round(row["ctr"] * 100, 2),
        "position": round(row["position"], 1),
    }

# --- Analysis ---

# 1. Ranking Opportunities (position 5-30, impressions >= 10)
ranking_opps = []
for row in all_queries:
    pos = row["position"]
    impr = row["impressions"]
    if 5 <= pos <= 30 and impr >= 10:
        q = row["keys"][0]
        # Classify niche
        niche = "General"
        for nk, nd in niche_data.items():
            if any(t in q.lower() for t in nd["terms"]):
                niche = nd["label"]
                break
        score = impr * (30 - pos) / 30
        ranking_opps.append({
            "query": q,
            "position": round(pos, 1),
            "impressions": impr,
            "clicks": row["clicks"],
            "ctr": round(row["ctr"] * 100, 2),
            "niche": niche,
            "priority_score": round(score, 1),
        })

ranking_opps.sort(key=lambda x: x["priority_score"], reverse=True)

# 2. Content Gaps
content_gaps = []
services = config["services_to_rank"]
niches = config["target_niches"]

for niche_key, niche_cfg in niches.items():
    label = niche_cfg["label"]
    for svc in services:
        # Check if any page targets this niche×service combo
        combo_terms = [label.lower().replace("&", "").split(), svc.lower().split()]
        flat_terms = [t for group in combo_terms for t in group]

        # Check if any existing page URL or content targets this
        has_page = False
        total_impressions = 0
        for url, data in existing_pages.items():
            url_lower = url.lower()
            if sum(1 for t in flat_terms if t in url_lower) >= 2:
                has_page = True
                break

        # Check GSC impressions for this combo
        for row in all_queries:
            q = row["keys"][0].lower()
            if sum(1 for t in flat_terms if t in q) >= 2:
                total_impressions += row["impressions"]

        if not has_page:
            # Determine priority
            if svc in ["paid media", "seo", "email marketing"]:
                priority = "High"
            elif svc in ["social media marketing", "content marketing", "web design"]:
                priority = "Medium"
            else:
                priority = "Low"

            # Build target keyword cluster
            kw_cluster = f"{label.lower()} {svc} agency"
            slug = f"{niche_key.replace('_', '-')}-{svc.lower().replace(' ', '-')}"

            content_gaps.append({
                "niche": label,
                "service": svc,
                "keyword_cluster": kw_cluster,
                "search_intent": "Commercial",
                "page_type": "Service Page" if priority == "High" else "Blog/Guide",
                "recommended_url": f"/{slug}/",
                "priority": priority,
                "current_impressions": total_impressions,
            })

content_gaps.sort(key=lambda x: ("High", "Medium", "Low").index(x["priority"]))

# 3. Quick Wins (position 1-5, low CTR)
quick_wins = []
expected_ctr = {1: 30, 2: 15, 3: 10, 4: 5, 5: 3}
for row in all_queries:
    pos = row["position"]
    if 1 <= pos <= 5.5 and row["impressions"] >= 20:
        pos_bucket = round(pos)
        if pos_bucket > 5:
            pos_bucket = 5
        exp = expected_ctr.get(pos_bucket, 3)
        actual_ctr = row["ctr"] * 100
        if actual_ctr < exp * 0.5:  # Less than half expected CTR
            quick_wins.append({
                "query": row["keys"][0],
                "position": round(pos, 1),
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "current_ctr": round(actual_ctr, 2),
                "expected_ctr": exp,
            })

quick_wins.sort(key=lambda x: x["impressions"], reverse=True)

# --- Output ---
output = {
    "generated": datetime.now().isoformat(),
    "date_range": f"{start_date} to {end_date}",
    "total_queries": len(all_queries),
    "total_pages": len(all_pages),
    "ranking_opportunities": ranking_opps[:100],
    "content_gaps": content_gaps,
    "quick_wins": quick_wins[:50],
    "niche_summary": {
        k: {"label": v["label"], "matching_queries": v["matching_queries"]}
        for k, v in niche_data.items()
    },
    "summary": {
        "total_ranking_opps": len(ranking_opps),
        "total_content_gaps": len(content_gaps),
        "total_quick_wins": len(quick_wins),
        "estimated_monthly_traffic_opp": sum(r["impressions"] * r["ctr"] / 100 for r in ranking_opps[:50]),
    },
}

# Print JSON to stdout for Claude to consume
print(json.dumps(output, indent=2))

# Also save to file
with open("scripts/seo_opportunities_output.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved to scripts/seo_opportunities_output.json", file=sys.stderr)
