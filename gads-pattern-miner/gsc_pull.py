"""
Pull GSC branded-query monthly history for a client domain — used by gads-pattern-miner
for TOF lift analysis (does TOF spend → branded organic search lift?).

Uses ADC at C:\\Users\\assem\\.claude\\secrets\\ga4-user-adc.json (marketing@ OAuth with
webmasters.readonly + analytics.readonly scopes).

Output: stdout monthly aggregate table + data/<client>_gsc.json (full raw rows).

Usage:
    python gsc_pull.py --client jinx --site "sc-domain:thinkjinx.com" --brand jinx --months 16
"""
import argparse
import io
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import google.auth
from googleapiclient.discovery import build

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ADC = r"C:\Users\assem\.claude\secrets\ga4-user-adc.json"
SKILL_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


def build_service():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ADC
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    return build("searchconsole", "v1", credentials=creds)


def pull_daily_branded(svc, site, brand, start, end):
    """Pull daily clicks/impr for queries containing `brand`. Returns rows of (date, query, clicks, impr, ctr, position)."""
    rows = []
    start_row = 0
    while True:
        body = {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "dimensions": ["date", "query"],
            "rowLimit": 25000,
            "startRow": start_row,
            "dimensionFilterGroups": [{
                "filters": [{"dimension": "query", "operator": "contains", "expression": brand}]
            }],
        }
        resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        batch = resp.get("rows", [])
        if not batch:
            break
        for r in batch:
            rows.append({
                "date": r["keys"][0],
                "query": r["keys"][1],
                "clicks": r["clicks"],
                "impressions": r["impressions"],
                "ctr": r["ctr"],
                "position": r["position"],
            })
        start_row += len(batch)
        if len(batch) < 25000:
            break
    return rows


def pull_monthly_totals(svc, site, start, end):
    """Whole-site monthly clicks/impressions (no filter) — for baseline context."""
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["date"],
        "rowLimit": 25000,
    }
    resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
    by_month = defaultdict(lambda: {"clicks": 0, "impressions": 0})
    for r in resp.get("rows", []):
        m = r["keys"][0][:7]
        by_month[m]["clicks"] += r["clicks"]
        by_month[m]["impressions"] += r["impressions"]
    return [{"month": k, **v} for k, v in sorted(by_month.items())]


def aggregate_monthly(rows):
    by_month = defaultdict(lambda: {"clicks": 0, "impressions": 0})
    for r in rows:
        m = r["date"][:7]
        by_month[m]["clicks"] += r["clicks"]
        by_month[m]["impressions"] += r["impressions"]
    return [{"month": k, **v} for k, v in sorted(by_month.items())]


def aggregate_by_query(rows, top_n=30):
    by_q = defaultdict(lambda: {"clicks": 0, "impressions": 0, "pos_sum_x_impr": 0.0})
    for r in rows:
        b = by_q[r["query"]]
        b["clicks"] += r["clicks"]
        b["impressions"] += r["impressions"]
        b["pos_sum_x_impr"] += r["position"] * r["impressions"]
    enriched = []
    for q, v in by_q.items():
        avg_pos = (v["pos_sum_x_impr"] / v["impressions"]) if v["impressions"] else 0
        enriched.append({"query": q, "clicks": v["clicks"], "impressions": v["impressions"], "avg_pos": round(avg_pos, 2)})
    return sorted(enriched, key=lambda x: -x["clicks"])[:top_n]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--client", required=True)
    p.add_argument("--site", required=True, help='GSC site URL e.g. sc-domain:thinkjinx.com')
    p.add_argument("--brand", required=True, help="Brand stem to filter queries (case-insensitive substring)")
    p.add_argument("--months", type=int, default=16, help="Months back from today (GSC max ~16)")
    args = p.parse_args()

    end = date.today() - timedelta(days=3)  # GSC lag ~2-3 days
    start = date(end.year - (1 if end.month - args.months % 12 <= 0 else 0), ((end.month - args.months) % 12) or 12, 1)
    # Simpler: use a 16-month-ish window from today
    start = date.today() - timedelta(days=args.months * 31)
    # Snap to first of month
    start = date(start.year, start.month, 1)

    svc = build_service()

    print(f"\n{'='*78}")
    print(f"GSC LIFT PULL — {args.client} — {args.site} — {start} to {end}")
    print(f"Brand filter: query CONTAINS '{args.brand}' (case-insensitive)")
    print(f"{'='*78}")

    branded = pull_daily_branded(svc, args.site, args.brand, start, end)
    print(f"Branded daily rows: {len(branded)}")

    total = pull_monthly_totals(svc, args.site, start, end)

    monthly_branded = aggregate_monthly(branded)
    top_queries = aggregate_by_query(branded, top_n=30)

    # Merge for side-by-side
    total_by_m = {r["month"]: r for r in total}
    branded_by_m = {r["month"]: r for r in monthly_branded}
    all_months = sorted(set(total_by_m.keys()) | set(branded_by_m.keys()))

    print(f"\n--- MONTHLY: total site vs branded subset ---")
    print(f"{'Month':<10} {'Site Impr':>11} {'Site Clk':>9} {'Brand Impr':>11} {'Brand Clk':>10} {'Brand %impr':>11}")
    for m in all_months:
        t = total_by_m.get(m, {"clicks": 0, "impressions": 0})
        b = branded_by_m.get(m, {"clicks": 0, "impressions": 0})
        pct = (b["impressions"] / t["impressions"] * 100) if t["impressions"] else 0
        print(f"{m:<10} {t['impressions']:>11,} {t['clicks']:>9,} {b['impressions']:>11,} {b['clicks']:>10,} {pct:>10.2f}%")

    print(f"\n--- TOP 30 BRANDED QUERIES (window total, by clicks) ---")
    print(f"{'Query':<55} {'Clicks':>7} {'Impr':>8} {'AvgPos':>7}")
    for q in top_queries:
        print(f"{q['query'][:55]:<55} {q['clicks']:>7,} {q['impressions']:>8,} {q['avg_pos']:>7.2f}")

    # Save raw
    raw_path = DATA_DIR / f"{args.client}_gsc.json"
    raw_path.write_text(json.dumps({
        "client": args.client,
        "site": args.site,
        "brand": args.brand,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "monthly_total": total,
        "monthly_branded": monthly_branded,
        "top_branded_queries": top_queries,
        "branded_daily": branded,
    }, indent=2))
    print(f"\nRaw saved: {raw_path}")


if __name__ == "__main__":
    main()
