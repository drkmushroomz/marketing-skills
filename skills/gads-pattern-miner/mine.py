"""
gads-pattern-miner — single-script mining pipeline.

Pulls Google Ads test data for one customer over N days, aggregates into
top-N tables, prints ONLY summaries to stdout (token-efficient), writes
the full raw JSON to data/<slug>_raw.json for deeper investigation.

Usage:
    python mine.py --client jinx --cid 5841094176 --days 90
"""
import argparse
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# --- Config -----------------------------------------------------------------

DEVELOPER_TOKEN = "mwAphl3Sdh0IUMPoOf342g"
LOGIN_CID = "1874174744"  # JF MCC

TOP_N_ASSETS = 25
TOP_N_TERMS = 30
TOP_N_KEYWORDS = 25
TOP_N_WASTE = 20
MIN_IMP_FOR_PATTERN = 100

SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


# --- Helpers ----------------------------------------------------------------

def load_client() -> GoogleAdsClient:
    tokens_path = Path("scripts/gads_tokens.json")
    with tokens_path.open() as f:
        tokens = json.load(f)
    return GoogleAdsClient.load_from_dict({
        "developer_token": DEVELOPER_TOKEN,
        "client_id": tokens["client_id"],
        "client_secret": tokens["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "login_customer_id": LOGIN_CID,
        "use_proto_plus": True,
    })


def enum_name(value) -> str:
    """Get the .name attribute of a proto-plus IntEnum; fall back to str()."""
    try:
        return value.name
    except AttributeError:
        return str(value)


def safe_div(num, denom):
    return (num / denom) if denom else 0.0


def chi_square_ctr(clicks_a, impr_a, clicks_b, impr_b) -> float:
    """Simple 2x2 chi-square — returns chi^2 statistic. df=1, p<0.05 at chi^2 > 3.84."""
    a, b = clicks_a, impr_a - clicks_a
    c, d = clicks_b, impr_b - clicks_b
    total = a + b + c + d
    if total == 0 or (a + b) == 0 or (c + d) == 0 or (a + c) == 0 or (b + d) == 0:
        return 0.0
    expected = [
        ((a + b) * (a + c) / total),
        ((a + b) * (b + d) / total),
        ((c + d) * (a + c) / total),
        ((c + d) * (b + d) / total),
    ]
    obs = [a, b, c, d]
    chi2 = sum(((o - e) ** 2 / e) if e else 0 for o, e in zip(obs, expected))
    return chi2


# --- Queries ----------------------------------------------------------------

def pull_account_overview(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            customer.id, customer.descriptive_name, customer.currency_code,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value
        FROM customer
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    out = {"customer_id": cid}
    try:
        resp = svc.search_stream(customer_id=cid, query=q)
        for batch in resp:
            for row in batch.results:
                out.update({
                    "name": row.customer.descriptive_name,
                    "currency": row.customer.currency_code,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost": row.metrics.cost_micros / 1_000_000,
                    "conversions": float(row.metrics.conversions),
                    "conv_value": float(row.metrics.conversions_value),
                })
    except Exception as e:
        out["error"] = str(e)
    return out


def pull_campaigns(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.advertising_channel_type, campaign.bidding_strategy_type,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.conversions_value, metrics.ctr
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """
    rows = []
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            rows.append({
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": enum_name(row.campaign.status),
                "type": enum_name(row.campaign.advertising_channel_type),
                "bid_strategy": enum_name(row.campaign.bidding_strategy_type),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": float(row.metrics.conversions),
                "conv_value": float(row.metrics.conversions_value),
                "ctr": row.metrics.ctr * 100,
            })
    return rows


def pull_asset_performance(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            campaign.name, ad_group.name,
            ad_group_ad_asset_view.field_type,
            ad_group_ad_asset_view.performance_label,
            asset.text_asset.text,
            metrics.impressions, metrics.clicks, metrics.conversions
        FROM ad_group_ad_asset_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND ad_group_ad_asset_view.field_type IN ('HEADLINE', 'DESCRIPTION')
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
        LIMIT 1000
    """
    rows = []
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            impr = row.metrics.impressions
            if impr == 0:
                continue
            rows.append({
                "label": enum_name(row.ad_group_ad_asset_view.performance_label),
                "field_type": enum_name(row.ad_group_ad_asset_view.field_type),
                "text": row.asset.text_asset.text or "",
                "impressions": impr,
                "clicks": row.metrics.clicks,
                "conversions": float(row.metrics.conversions),
                "campaign": row.campaign.name,
            })
    return rows


def pull_search_terms(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            search_term_view.search_term, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM search_term_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND metrics.impressions > 2
        ORDER BY metrics.cost_micros DESC
        LIMIT 1000
    """
    rows = []
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            rows.append({
                "term": row.search_term_view.search_term,
                "campaign": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": float(row.metrics.conversions),
                "ctr": row.metrics.ctr * 100,
            })
    return rows


def pull_keywords(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
            campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM keyword_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND ad_group_criterion.status != 'REMOVED'
            AND metrics.impressions > 5
        ORDER BY metrics.cost_micros DESC
        LIMIT 500
    """
    rows = []
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            rows.append({
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": enum_name(row.ad_group_criterion.keyword.match_type),
                "campaign": row.campaign.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": float(row.metrics.conversions),
                "ctr": row.metrics.ctr * 100,
            })
    return rows


def pull_video_metrics(client, cid, start, end):
    """TOF metrics by campaign for VIDEO/DEMAND_GEN. video_views/view_rate live at ad_group_ad
    level (not campaign), so we pull CPM + quartile completion at campaign level, then derive
    view-rate-ish metric via ad_group_ad summation."""
    svc = client.get_service("GoogleAdsService")

    # Campaign-level: CPM and quartile completion (these work on campaign in v23)
    q_camp = f"""
        SELECT
            campaign.name, campaign.advertising_channel_type,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.average_cpm,
            metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate,
            metrics.video_quartile_p75_rate, metrics.video_quartile_p100_rate
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND campaign.advertising_channel_type IN ('VIDEO', 'DEMAND_GEN')
        ORDER BY metrics.cost_micros DESC
    """
    camp_rows = {}
    for batch in svc.search_stream(customer_id=cid, query=q_camp):
        for row in batch.results:
            camp_rows[row.campaign.name] = {
                "campaign": row.campaign.name,
                "type": enum_name(row.campaign.advertising_channel_type),
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "cpm": row.metrics.average_cpm / 1_000_000 if row.metrics.average_cpm else 0,
                "q25": row.metrics.video_quartile_p25_rate * 100 if row.metrics.video_quartile_p25_rate else 0,
                "q50": row.metrics.video_quartile_p50_rate * 100 if row.metrics.video_quartile_p50_rate else 0,
                "q75": row.metrics.video_quartile_p75_rate * 100 if row.metrics.video_quartile_p75_rate else 0,
                "q100": row.metrics.video_quartile_p100_rate * 100 if row.metrics.video_quartile_p100_rate else 0,
                "video_views": 0,
                "view_rate": 0.0,
                "cpv": 0.0,
            }

    # Ad-group-ad level: views + view_rate + CPV, aggregated up to campaign
    q_views = f"""
        SELECT
            campaign.name,
            metrics.video_views, metrics.video_view_rate, metrics.average_cpv,
            metrics.impressions
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND campaign.advertising_channel_type IN ('VIDEO', 'DEMAND_GEN')
            AND metrics.impressions > 0
    """
    try:
        view_agg = defaultdict(lambda: {"views": 0, "impr_weighted_vr": 0.0, "impr": 0, "cost_weighted_cpv": 0.0, "views_for_cpv": 0})
        for batch in svc.search_stream(customer_id=cid, query=q_views):
            for row in batch.results:
                cname = row.campaign.name
                views = row.metrics.video_views
                vr = row.metrics.video_view_rate * 100 if row.metrics.video_view_rate else 0
                cpv = row.metrics.average_cpv / 1_000_000 if row.metrics.average_cpv else 0
                impr = row.metrics.impressions
                view_agg[cname]["views"] += views
                view_agg[cname]["impr_weighted_vr"] += vr * impr
                view_agg[cname]["impr"] += impr
                view_agg[cname]["cost_weighted_cpv"] += cpv * views
                view_agg[cname]["views_for_cpv"] += views
        for cname, agg in view_agg.items():
            if cname in camp_rows:
                camp_rows[cname]["video_views"] = agg["views"]
                camp_rows[cname]["view_rate"] = (agg["impr_weighted_vr"] / agg["impr"]) if agg["impr"] else 0
                camp_rows[cname]["cpv"] = (agg["cost_weighted_cpv"] / agg["views_for_cpv"]) if agg["views_for_cpv"] else 0
    except Exception as e:
        # Demand Gen may not expose video_views on ad_group_ad — non-fatal
        for r in camp_rows.values():
            r["_view_query_error"] = str(e)

    return list(camp_rows.values())


def pull_branded_monthly(client, cid, start, end, brand_term="jinx"):
    """Month-over-month branded search impressions — the TOF lift proxy."""
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            segments.month,
            metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
        FROM search_term_view
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND search_term_view.search_term LIKE '%{brand_term}%'
    """
    by_month = defaultdict(lambda: {"impressions": 0, "clicks": 0, "cost": 0, "conv": 0.0})
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            m = str(row.segments.month)
            by_month[m]["impressions"] += row.metrics.impressions
            by_month[m]["clicks"] += row.metrics.clicks
            by_month[m]["cost"] += row.metrics.cost_micros / 1_000_000
            by_month[m]["conv"] += float(row.metrics.conversions)
    return [{"month": k, **v} for k, v in sorted(by_month.items())]


def pull_conv_by_category(client, cid, start, end):
    """Split conv totals by category — separates STORE_VISIT from PURCHASE etc."""
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            segments.conversion_action_category,
            metrics.conversions, metrics.conversions_value
        FROM customer
        WHERE segments.date BETWEEN '{start}' AND '{end}'
    """
    rows = []
    try:
        for batch in svc.search_stream(customer_id=cid, query=q):
            for row in batch.results:
                rows.append({
                    "category": enum_name(row.segments.conversion_action_category),
                    "conversions": round(float(row.metrics.conversions), 1),
                    "value": round(float(row.metrics.conversions_value), 2),
                })
    except Exception as e:
        rows.append({"error": str(e)})
    return rows


def pull_ads(client, cid, start, end):
    svc = client.get_service("GoogleAdsService")
    q = f"""
        SELECT
            ad_group_ad.ad.id, ad_group_ad.ad.type,
            campaign.name, ad_group.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.ctr
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
            AND ad_group_ad.status != 'REMOVED'
            AND metrics.impressions > 0
        ORDER BY metrics.impressions DESC
        LIMIT 500
    """
    rows = []
    for batch in svc.search_stream(customer_id=cid, query=q):
        for row in batch.results:
            rows.append({
                "ad_id": row.ad_group_ad.ad.id,
                "ad_type": enum_name(row.ad_group_ad.ad.type_),
                "campaign": row.campaign.name,
                "ad_group": row.ad_group.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost": row.metrics.cost_micros / 1_000_000,
                "conversions": float(row.metrics.conversions),
                "ctr": row.metrics.ctr * 100,
            })
    return rows


# --- Aggregations -----------------------------------------------------------

def aggregate_assets(assets):
    """Asset patterns: BEST vs LOW, with text-pattern n-grams over winners/losers."""
    by_label = defaultdict(lambda: {"count": 0, "impr": 0, "clicks": 0, "conv": 0.0, "texts": []})
    for a in assets:
        bucket = by_label[(a["field_type"], a["label"])]
        bucket["count"] += 1
        bucket["impr"] += a["impressions"]
        bucket["clicks"] += a["clicks"]
        bucket["conv"] += a["conversions"]
        bucket["texts"].append(a["text"])

    summary = {}
    for (ftype, label), v in by_label.items():
        summary[f"{ftype}_{label}"] = {
            "count": v["count"],
            "impressions": v["impr"],
            "clicks": v["clicks"],
            "ctr": safe_div(v["clicks"], v["impr"]) * 100,
            "conversions": round(v["conv"], 1),
            "cvr": safe_div(v["conv"], v["clicks"]) * 100,
        }

    # Top BEST/LOW by impressions for human eyeball
    best = sorted([a for a in assets if a["label"] == "BEST"], key=lambda x: -x["impressions"])[:TOP_N_ASSETS]
    low = sorted([a for a in assets if a["label"] == "LOW"], key=lambda x: -x["impressions"])[:TOP_N_ASSETS]

    return {"by_label": summary, "top_best": best, "top_low": low}


def ngram_search_terms(terms, n=2, top=15):
    """Find recurring n-grams in conv-heavy vs zero-conv terms."""
    def ngrams(text, n):
        words = re.findall(r"\w+", text.lower())
        return [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]

    conv_terms = [t for t in terms if t["conversions"] > 0]
    zero_conv_spend = [t for t in terms if t["conversions"] == 0 and t["cost"] > 5]

    conv_grams = Counter()
    for t in conv_terms:
        for g in ngrams(t["term"], n):
            conv_grams[g] += int(t["conversions"])

    waste_grams = Counter()
    for t in zero_conv_spend:
        for g in ngrams(t["term"], n):
            waste_grams[g] += round(t["cost"], 2)

    return {
        f"top_{n}gram_conv": conv_grams.most_common(top),
        f"top_{n}gram_waste": waste_grams.most_common(top),
    }


def aggregate_search_terms(terms):
    by_spend = sorted(terms, key=lambda x: -x["cost"])[:TOP_N_TERMS]
    by_conv = sorted([t for t in terms if t["conversions"] > 0], key=lambda x: -x["conversions"])[:TOP_N_TERMS]
    waste = sorted([t for t in terms if t["conversions"] == 0 and t["cost"] > 0],
                   key=lambda x: -x["cost"])[:TOP_N_WASTE]
    return {
        "top_by_spend": by_spend,
        "top_by_conv": by_conv,
        "top_waste_zero_conv": waste,
        "ngrams_bigram": ngram_search_terms(terms, n=2),
        "ngrams_trigram": ngram_search_terms(terms, n=3),
    }


def aggregate_keywords(kws):
    by_conv = sorted([k for k in kws if k["conversions"] > 0], key=lambda x: -x["conversions"])[:TOP_N_KEYWORDS]
    by_waste = sorted([k for k in kws if k["conversions"] == 0 and k["cost"] > 5],
                      key=lambda x: -x["cost"])[:TOP_N_WASTE]
    by_ctr = sorted([k for k in kws if k["impressions"] >= MIN_IMP_FOR_PATTERN],
                    key=lambda x: -x["ctr"])[:TOP_N_KEYWORDS]
    return {"top_converters": by_conv, "top_waste": by_waste, "top_ctr": by_ctr}


def aggregate_campaigns(camps):
    total_cost = sum(c["cost"] for c in camps)
    total_conv = sum(c["conversions"] for c in camps)
    enriched = []
    for c in camps:
        c2 = dict(c)
        c2["spend_share"] = safe_div(c["cost"], total_cost) * 100
        c2["cpa"] = safe_div(c["cost"], c["conversions"])
        c2["roas"] = safe_div(c["conv_value"], c["cost"])
        enriched.append(c2)
    return {
        "totals": {"cost": round(total_cost, 2), "conversions": round(total_conv, 1)},
        "campaigns": enriched,
    }


# --- Stdout (token-budgeted) ------------------------------------------------

def print_tof_summary(video_rows, branded_monthly, conv_by_cat, brand_term):
    print(f"\n--- CONVERSION CATEGORY BREAKDOWN ---")
    print(f"{'Category':<28} {'Conv':>10} {'Value':>10}")
    for r in conv_by_cat:
        if "error" in r:
            print(f"  (error: {r['error']})")
        else:
            print(f"{r['category']:<28} {r['conversions']:>10,.1f} ${r['value']:>9,.0f}")

    print(f"\n--- BRANDED MONTHLY TREND (search term LIKE '%{brand_term}%') ---")
    print(f"{'Month':<10} {'Impr':>10} {'Clicks':>8} {'Spend':>9} {'Conv':>7}")
    for r in branded_monthly:
        print(f"{r['month']:<10} {r['impressions']:>10,} {r['clicks']:>8,} "
              f"${r['cost']:>7,.0f} {r['conv']:>7.1f}")

    print(f"\n--- VIDEO / DEMAND GEN CAMPAIGNS — TOF METRICS ---")
    print(f"{'Campaign':<42} {'Type':<11} {'Spend':>8} {'Impr':>10} {'CPM':>6} {'CPV':>5} {'VR%':>5} {'Q25':>5} {'Q100':>5}")
    for v in sorted(video_rows, key=lambda x: -x["cost"])[:15]:
        print(f"{v['campaign'][:40]:<42} {v['type'][:9]:<11} ${v['cost']:>6,.0f} {v['impressions']:>10,} "
              f"${v['cpm']:>4.2f} ${v['cpv']:>3.2f} {v['view_rate']:>4.1f}% {v['q25']:>4.1f}% {v['q100']:>4.1f}%")


def print_summary(slug, days, overview, camps_agg, assets_agg, terms_agg, kws_agg, ads_count):
    print(f"\n{'='*78}")
    print(f"GADS PATTERN MINER — {slug} — last {days}d")
    print(f"{'='*78}")
    if "error" in overview:
        print(f"ERROR pulling overview: {overview['error']}")
    print(f"Account: {overview.get('name','?')} ({overview['customer_id']}) | {overview.get('currency','?')}")
    print(f"Spend: ${overview.get('cost',0):,.2f} | Conv: {overview.get('conversions',0):.1f} "
          f"| Clicks: {overview.get('clicks',0):,} | Impr: {overview.get('impressions',0):,}")
    print(f"Ads tracked: {ads_count}")

    print(f"\n--- CAMPAIGNS ({len(camps_agg['campaigns'])}) — spend desc ---")
    print(f"{'Name':<45} {'Type':<10} {'Spend':>9} {'Conv':>6} {'CPA':>8} {'CTR%':>6} {'Bid':<14}")
    for c in camps_agg["campaigns"][:12]:
        print(f"{c['name'][:43]:<45} {c['type'][:8]:<10} ${c['cost']:>7,.0f} {c['conversions']:>6.1f} "
              f"${c['cpa']:>6,.0f} {c['ctr']:>5.2f}% {c['bid_strategy'][:13]:<14}")

    print(f"\n--- ASSET LABEL ROLLUP ---")
    print(f"{'Bucket':<25} {'N':>5} {'Impr':>10} {'CTR%':>6} {'CVR%':>6}")
    for k, v in sorted(assets_agg["by_label"].items()):
        print(f"{k:<25} {v['count']:>5} {v['impressions']:>10,} {v['ctr']:>5.2f}% {v['cvr']:>5.2f}%")

    print(f"\n--- TOP BEST-LABEL ASSETS (by impressions) ---")
    for a in assets_agg["top_best"][:TOP_N_ASSETS]:
        print(f"  [{a['field_type'][:4]}] {a['text'][:65]:<65} impr={a['impressions']:>7,} clicks={a['clicks']:>4}")
    print(f"\n--- TOP LOW-LABEL ASSETS (by impressions) ---")
    for a in assets_agg["top_low"][:TOP_N_ASSETS]:
        print(f"  [{a['field_type'][:4]}] {a['text'][:65]:<65} impr={a['impressions']:>7,} clicks={a['clicks']:>4}")

    print(f"\n--- TOP SEARCH TERMS BY CONV ---")
    for t in terms_agg["top_by_conv"][:TOP_N_TERMS]:
        print(f"  {t['term'][:55]:<55} conv={t['conversions']:>5.1f} spend=${t['cost']:>6,.0f} ctr={t['ctr']:>5.2f}%")
    print(f"\n--- TOP WASTE TERMS (zero conv, >=$1 spend) ---")
    for t in terms_agg["top_waste_zero_conv"][:TOP_N_WASTE]:
        print(f"  {t['term'][:55]:<55} spend=${t['cost']:>6,.0f} clicks={t['clicks']:>4} ctr={t['ctr']:>5.2f}%")

    print(f"\n--- BIGRAM PATTERNS ---")
    print(f"  Converting bigrams: {terms_agg['ngrams_bigram']['top_2gram_conv']}")
    print(f"  Waste bigrams:      {terms_agg['ngrams_bigram']['top_2gram_waste']}")

    print(f"\n--- TOP CONVERTING KEYWORDS ---")
    for k in kws_agg["top_converters"][:TOP_N_KEYWORDS]:
        print(f"  [{k['match_type'][:5]:<5}] {k['keyword'][:50]:<50} conv={k['conversions']:>5.1f} "
              f"spend=${k['cost']:>6,.0f}")
    print(f"\n--- TOP WASTE KEYWORDS (zero conv, >=$5 spend) ---")
    for k in kws_agg["top_waste"][:TOP_N_WASTE]:
        print(f"  [{k['match_type'][:5]:<5}] {k['keyword'][:50]:<50} spend=${k['cost']:>6,.0f} "
              f"clicks={k['clicks']:>4}")

    print(f"\n{'='*78}")
    print("Stdout end. Full raw data at data/<slug>_raw.json (do NOT read into context unless investigating).")
    print(f"{'='*78}\n")


# --- Main -------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--client", required=True, help="Client slug (e.g. jinx)")
    p.add_argument("--cid", required=True, help="Google Ads customer ID (no dashes)")
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--kpi-type", choices=["dtc", "tof", "retail", "lead-gen"], default="dtc",
                   help="KPI lens for output framing. tof/retail prints video metrics + branded trend.")
    p.add_argument("--brand-term", default=None, help="Brand stem for branded trend (defaults to --client)")
    args = p.parse_args()

    end = date.today()
    start = end - timedelta(days=args.days)

    client = load_client()

    brand_term = (args.brand_term or args.client).lower()

    overview = pull_account_overview(client, args.cid, start, end)
    camps = pull_campaigns(client, args.cid, start, end)
    assets = pull_asset_performance(client, args.cid, start, end)
    terms = pull_search_terms(client, args.cid, start, end)
    kws = pull_keywords(client, args.cid, start, end)
    ads = pull_ads(client, args.cid, start, end)

    # TOF / retail additions
    video = pull_video_metrics(client, args.cid, start, end) if args.kpi_type in ("tof", "retail") else []
    branded_monthly = pull_branded_monthly(client, args.cid, start, end, brand_term) \
        if args.kpi_type in ("tof", "retail") else []
    conv_by_cat = pull_conv_by_category(client, args.cid, start, end) \
        if args.kpi_type in ("tof", "retail") else []

    camps_agg = aggregate_campaigns(camps)
    assets_agg = aggregate_assets(assets)
    terms_agg = aggregate_search_terms(terms)
    kws_agg = aggregate_keywords(kws)

    raw = {
        "client": args.client,
        "customer_id": args.cid,
        "date_range": f"{start} to {end}",
        "kpi_type": args.kpi_type,
        "overview": overview,
        "campaigns": camps,
        "assets": assets,
        "search_terms": terms,
        "keywords": kws,
        "ads": ads,
        "video_metrics": video,
        "branded_monthly": branded_monthly,
        "conv_by_category": conv_by_cat,
    }
    raw_path = DATA_DIR / f"{args.client}_raw.json"
    raw_path.write_text(json.dumps(raw, indent=2))

    print_summary(args.client, args.days, overview, camps_agg, assets_agg, terms_agg, kws_agg, len(ads))
    if args.kpi_type in ("tof", "retail"):
        print_tof_summary(video, branded_monthly, conv_by_cat, brand_term)
    print(f"\nRaw JSON: {raw_path}")


if __name__ == "__main__":
    main()
