"""
Pull keyword performance data from Google Ads account 909-908-1672.
Uses GAQL (Google Ads Query Language) to get search term and keyword reports.
"""
import json
from google.ads.googleads.client import GoogleAdsClient

CUSTOMER_ID = "9099081672"
DEVELOPER_TOKEN = "mwAphl3Sdh0IUMPoOf342g"

with open("scripts/gads_tokens.json") as f:
    tokens = json.load(f)

config = {
    "developer_token": DEVELOPER_TOKEN,
    "client_id": tokens["client_id"],
    "client_secret": tokens["client_secret"],
    "refresh_token": tokens["refresh_token"],
    "login_customer_id": "1874174744",
    "use_proto_plus": True,
}

client = GoogleAdsClient.load_from_dict(config)
ga_service = client.get_service("GoogleAdsService")

# --- 1. Active campaign keywords with performance (last 90 days) ---
print("=" * 80)
print("GOOGLE ADS KEYWORDS — Account 909-908-1672 (Last 90 days)")
print("=" * 80)

keyword_query = """
    SELECT
        campaign.name,
        campaign.status,
        ad_group.name,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros,
        metrics.ctr,
        metrics.average_cpc,
        metrics.conversions_from_interactions_rate
    FROM keyword_view
    WHERE segments.date BETWEEN '2025-12-22' AND '2026-03-22'
        AND campaign.status != 'REMOVED'
        AND ad_group_criterion.status != 'REMOVED'
    ORDER BY metrics.impressions DESC
    LIMIT 200
"""

print("\n### KEYWORD PERFORMANCE ###\n")
print(f"{'Keyword':<40} {'Match':<12} {'Campaign':<30} {'Impr':>8} {'Clicks':>8} {'Conv':>8} {'CTR':>8} {'CPC':>8} {'Conv%':>8}")
print("-" * 140)

try:
    response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=keyword_query)
    keyword_count = 0
    keywords_list = []
    for batch in response:
        for row in batch.results:
            keyword_count += 1
            kw = row.ad_group_criterion.keyword.text
            match = str(row.ad_group_criterion.keyword.match_type).replace("KeywordMatchType.", "")
            campaign = row.campaign.name
            impr = row.metrics.impressions
            clicks = row.metrics.clicks
            conv = row.metrics.conversions
            ctr = row.metrics.ctr * 100
            cpc = row.metrics.average_cpc / 1_000_000 if row.metrics.average_cpc else 0
            conv_rate = row.metrics.conversions_from_interactions_rate * 100
            cost = row.metrics.cost_micros / 1_000_000

            print(f"{kw:<40} {match:<12} {campaign:<30} {impr:>8} {clicks:>8} {conv:>8.1f} {ctr:>7.2f}% ${cpc:>6.2f} {conv_rate:>7.2f}%")
            keywords_list.append({
                "keyword": kw,
                "match_type": match,
                "campaign": campaign,
                "impressions": impr,
                "clicks": clicks,
                "conversions": float(conv),
                "ctr": float(ctr),
                "cpc": float(cpc),
                "conv_rate": float(conv_rate),
                "cost": float(cost),
            })

    print(f"\nTotal keywords: {keyword_count}")
except Exception as e:
    print(f"Error fetching keywords: {e}")
    keywords_list = []

# --- 2. Search terms report (what people actually searched) ---
print("\n" + "=" * 80)
print("SEARCH TERMS REPORT (Last 90 days)")
print("=" * 80)

search_terms_query = """
    SELECT
        search_term_view.search_term,
        campaign.name,
        metrics.impressions,
        metrics.clicks,
        metrics.conversions,
        metrics.cost_micros,
        metrics.ctr,
        metrics.conversions_from_interactions_rate
    FROM search_term_view
    WHERE segments.date BETWEEN '2025-12-22' AND '2026-03-22'
        AND campaign.status != 'REMOVED'
    ORDER BY metrics.impressions DESC
    LIMIT 200
"""

print(f"\n{'Search Term':<50} {'Campaign':<30} {'Impr':>8} {'Clicks':>8} {'Conv':>8} {'CTR':>8} {'Conv%':>8}")
print("-" * 130)

search_terms_list = []
try:
    response = ga_service.search_stream(customer_id=CUSTOMER_ID, query=search_terms_query)
    st_count = 0
    for batch in response:
        for row in batch.results:
            st_count += 1
            term = row.search_term_view.search_term
            campaign = row.campaign.name
            impr = row.metrics.impressions
            clicks = row.metrics.clicks
            conv = row.metrics.conversions
            ctr = row.metrics.ctr * 100
            conv_rate = row.metrics.conversions_from_interactions_rate * 100
            cost = row.metrics.cost_micros / 1_000_000

            print(f"{term:<50} {campaign:<30} {impr:>8} {clicks:>8} {conv:>8.1f} {ctr:>7.2f}% {conv_rate:>7.2f}%")
            search_terms_list.append({
                "search_term": term,
                "campaign": campaign,
                "impressions": impr,
                "clicks": clicks,
                "conversions": float(conv),
                "ctr": float(ctr),
                "conv_rate": float(conv_rate),
                "cost": float(cost),
            })
    print(f"\nTotal search terms: {st_count}")
except Exception as e:
    print(f"Error fetching search terms: {e}")

# Save both to JSON for cross-referencing
output = {
    "keywords": keywords_list,
    "search_terms": search_terms_list,
}
with open("scripts/gads_data.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"\nData saved to scripts/gads_data.json")
