"""Pull GSC data and save to JSON, then do cross-reference."""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
SITE_URL = "sc-domain:trainwithdaveoc.com"

with open("scripts/gads_tokens.json") as f:
    tokens = json.load(f)

creds = Credentials(
    token=tokens.get("access_token"),
    refresh_token=tokens["refresh_token"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
)

service = build("searchconsole", "v1", credentials=creds)

# Pull all query data
all_rows = []
start_row = 0
while True:
    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body={
            "startDate": "2025-12-22",
            "endDate": "2026-03-22",
            "dimensions": ["query"],
            "rowLimit": 1000,
            "startRow": start_row,
        },
    ).execute()
    rows = response.get("rows", [])
    if not rows:
        break
    all_rows.extend(rows)
    start_row += len(rows)
    if len(rows) < 1000:
        break

gsc_data = []
for row in all_rows:
    gsc_data.append({
        "query": row["keys"][0],
        "clicks": row["clicks"],
        "impressions": row["impressions"],
        "ctr": round(row["ctr"] * 100, 2),
        "position": round(row["position"], 1),
    })

with open("scripts/gsc_data.json", "w") as f:
    json.dump(gsc_data, f, indent=2)

print(f"Saved {len(gsc_data)} queries to scripts/gsc_data.json")

# --- CROSS-REFERENCE ---
with open("scripts/gads_data.json") as f:
    gads = json.load(f)

ads_keywords = set()
ads_lookup = {}
for kw in gads.get("keywords", []):
    k = kw["keyword"].lower().strip()
    ads_keywords.add(k)
    if k not in ads_lookup:
        ads_lookup[k] = {"clicks": 0, "cost": 0, "impressions": 0, "conversions": 0}
    ads_lookup[k]["clicks"] += kw["clicks"]
    ads_lookup[k]["cost"] += kw["cost"]
    ads_lookup[k]["impressions"] += kw["impressions"]
    ads_lookup[k]["conversions"] += kw["conversions"]

for st in gads.get("search_terms", []):
    k = st["search_term"].lower().strip()
    ads_keywords.add(k)

# 1. Organic winners NOT in ads
print("\n" + "=" * 110)
print("1. ORGANIC WINNERS NOT IN GOOGLE ADS (top 50 by clicks)")
print("=" * 110)
print(f"{'Query':<60} {'Org Clk':>8} {'Org Impr':>9} {'CTR':>7} {'Pos':>6}")
print("-" * 95)

missing = [r for r in sorted(gsc_data, key=lambda x: x["clicks"], reverse=True)
           if r["query"].lower().strip() not in ads_keywords and r["clicks"] >= 3]

for row in missing[:50]:
    print(f"{row['query']:<60} {row['clicks']:>8} {row['impressions']:>9} {row['ctr']:>6.1f}% {row['position']:>5.1f}")
print(f"\nTotal organic queries with 3+ clicks missing from ads: {len(missing)}")

# 2. Overlap: in both organic and paid
print("\n" + "=" * 110)
print("2. OVERLAP: QUERIES IN BOTH ORGANIC AND PAID")
print("=" * 110)
print(f"{'Query':<50} {'Org Clk':>8} {'Org Pos':>8} {'Ad Clk':>8} {'Ad Cost':>10} {'Ad Conv':>8}")
print("-" * 96)

overlap = []
for row in sorted(gsc_data, key=lambda x: x["clicks"], reverse=True):
    q = row["query"].lower().strip()
    if q in ads_lookup and row["clicks"] >= 1:
        ad = ads_lookup[q]
        overlap.append({**row, "ad_clicks": ad["clicks"], "ad_cost": ad["cost"], "ad_conv": ad["conversions"]})
        if len(overlap) <= 40:
            print(f"{row['query']:<50} {row['clicks']:>8} {row['position']:>7.1f} {ad['clicks']:>8} ${ad['cost']:>8.2f} {ad['conversions']:>7.1f}")

# 3. High-impression organic queries at position 5-20 (opportunity)
print("\n" + "=" * 110)
print("3. ORGANIC OPPORTUNITY KEYWORDS (Position 5-20, High Impressions)")
print("=" * 110)
print(f"{'Query':<60} {'Clk':>6} {'Impr':>8} {'CTR':>7} {'Pos':>6} {'In Ads':>7}")
print("-" * 98)

opps = [r for r in sorted(gsc_data, key=lambda x: x["impressions"], reverse=True)
        if 5 <= r["position"] <= 20 and r["impressions"] >= 50]

for row in opps[:40]:
    in_ads = "Yes" if row["query"].lower().strip() in ads_keywords else "NO"
    print(f"{row['query']:<60} {row['clicks']:>6} {row['impressions']:>8} {row['ctr']:>6.1f}% {row['position']:>5.1f} {in_ads:>7}")

print(f"\nTotal opportunity keywords: {len(opps)}")
