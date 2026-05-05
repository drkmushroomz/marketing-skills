#!/usr/bin/env python3
"""
Competitor Gap Analysis — Find keywords competitors rank for that you don't.

Pulls organic keywords from Ahrefs for your domain and competitors,
cross-references them, and surfaces gaps sorted by opportunity.

Usage:
    python competitor_gap.py
    python competitor_gap.py --competitors=singlegrain.com,webfx.com
    python competitor_gap.py --json

Environment variables:
    AHREFS_TOKEN    — Ahrefs API v3 token (required)
    YOUR_DOMAIN     — Your domain (default: jetfuel.agency)
    COMPETITORS     — Comma-separated competitor domains
    OUTPUT_DIR      — Where to save output (default: ./output)
"""

import json
import os
import sys
import requests
from collections import defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AHREFS_TOKEN = os.environ.get("AHREFS_TOKEN", "")
AHREFS_BASE = "https://api.ahrefs.com/v3"

YOUR_DOMAIN = os.environ.get("YOUR_DOMAIN", "jetfuel.agency")

DEFAULT_COMPETITORS = [
    "singlegrain.com",
    "webfx.com",
    "hawksem.com",
    "tinuiti.com",
    "commonthreadco.com",
]

_comp_env = os.environ.get("COMPETITORS", "")
COMPETITORS = [c.strip() for c in _comp_env.split(",") if c.strip()] if _comp_env else DEFAULT_COMPETITORS

# ─────────────────────────────────────────────
# Relevance filtering
# ─────────────────────────────────────────────

# Keywords must contain at least one of these to be considered relevant
RELEVANT_TERMS = {
    # Services
    "marketing", "agency", "seo", "ppc", "paid media", "paid search",
    "paid social", "content", "email", "social media", "ecommerce",
    "advertising", "ads", "campaign", "conversion", "cro", "analytics",
    "branding", "creative", "design", "web design", "landing page",

    # Industries (Jetfuel niches)
    "cpg", "food", "beverage", "health", "wellness", "supplement",
    "beauty", "skincare", "cosmetics", "dtc", "direct to consumer",
    "retail media", "amazon", "shopify",

    # Commercial intent
    "agency", "company", "service", "services", "firm", "consultant",
    "hire", "pricing", "cost", "best", "top", "vs", "alternative",
    "review", "platform", "tool", "software",

    # Strategy
    "strategy", "growth", "roi", "roas", "funnel", "lead gen",
    "demand gen", "retention", "acquisition", "optimization",
}

# Block noisy/irrelevant keywords
BLOCKLIST = {
    "login", "sign up", "sign in", "free trial", "coupon", "promo code",
    "salary", "jobs", "careers", "hiring", "internship",
    "wikipedia", "definition of",
    "photo search", "reverse image", "image search",
    "paragraph generator", "essay writer", "grammar checker",
    "word counter", "character counter", "spell checker",
    "ai detector", "plagiarism checker", "text humanizer",
    "paraphrasing tool", "rewording tool",
}


def is_relevant(keyword):
    """Check if a keyword is relevant to Jetfuel's business."""
    kw = keyword.lower()
    if any(blocked in kw for blocked in BLOCKLIST):
        return False
    if not any(term in kw for term in RELEVANT_TERMS):
        return False
    return True


# ─────────────────────────────────────────────
# Ahrefs API
# ─────────────────────────────────────────────

def fetch_organic_keywords(domain, limit=500):
    """Pull organic keywords for a domain from Ahrefs."""
    if not AHREFS_TOKEN:
        print(f"  [ERROR] No AHREFS_TOKEN set", file=sys.stderr)
        return []

    first_of_month = date.today().replace(day=1).strftime("%Y-%m-%d")

    try:
        resp = requests.get(
            f"{AHREFS_BASE}/site-explorer/organic-keywords",
            headers={"Authorization": f"Bearer {AHREFS_TOKEN}"},
            params={
                "target": domain,
                "country": "us",
                "date": first_of_month,
                "select": "keyword,volume,best_position,keyword_difficulty,sum_traffic,best_position_url,is_commercial,is_transactional",
                "order_by": "sum_traffic:desc",
                "limit": limit,
                "mode": "subdomains",
            },
            timeout=60,
        )

        if resp.status_code == 200:
            data = resp.json()
            keywords = data.get("keywords", [])
            print(f"  {domain}: {len(keywords)} organic keywords", file=sys.stderr)
            return keywords
        else:
            error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            print(f"  [WARN] Ahrefs {domain}: HTTP {resp.status_code} — {error}", file=sys.stderr)
            return []

    except Exception as e:
        print(f"  [WARN] Ahrefs {domain} error: {e}", file=sys.stderr)
        return []


def enrich_gaps_with_explorer(gap_keywords, batch_size=50):
    """Pull additional data (CPC, intents) for gap keywords via Keywords Explorer."""
    if not AHREFS_TOKEN or not gap_keywords:
        return {}

    enriched = {}
    kw_list = [g["keyword"] for g in gap_keywords[:200]]  # cap at 200

    for i in range(0, len(kw_list), batch_size):
        batch = kw_list[i:i + batch_size]
        try:
            resp = requests.get(
                f"{AHREFS_BASE}/keywords-explorer/overview",
                headers={"Authorization": f"Bearer {AHREFS_TOKEN}"},
                params={
                    "select": "keyword,volume,difficulty,cpc,traffic_potential,intents",
                    "keywords": ",".join(batch),
                    "country": "us",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                for kw_data in resp.json().get("keywords", []):
                    kw = kw_data.get("keyword", "").lower()
                    enriched[kw] = kw_data
        except Exception as e:
            print(f"  [WARN] Keywords Explorer batch error: {e}", file=sys.stderr)

    return enriched


# ─────────────────────────────────────────────
# Gap Analysis
# ─────────────────────────────────────────────

def funnel_stage(keyword, intents=None):
    """Classify keyword into BOFU/MOFU/TOFU."""
    kw = keyword.lower()

    bofu = ["agency", "services", "hire", "pricing", "cost", "company",
            "firms", "best", " vs ", "alternative", "platform", "tool",
            "software", "consultant", "outsource", "near me"]
    mofu = ["how to", "guide", "strategy", "examples", "case study",
            "roi", "template", "checklist", "tips", "framework",
            "what is", "comparison"]

    if intents:
        if intents.get("commercial") or intents.get("transactional"):
            return "BOFU"

    if any(t in kw for t in bofu):
        return "BOFU"
    if any(t in kw for t in mofu):
        return "MOFU"
    return "TOFU"


def find_gaps(my_keywords, competitor_data):
    """Find keywords where competitors rank top 20 and you rank > 50 or don't rank."""
    my_positions = {}
    for item in my_keywords:
        kw = item.get("keyword", "").lower()
        pos = item.get("best_position", 999)
        my_positions[kw] = pos

    gaps = []
    seen = set()

    for comp_domain, comp_keywords in competitor_data.items():
        for item in comp_keywords:
            kw = item.get("keyword", "").lower()
            if not kw or kw in seen:
                continue
            if not is_relevant(kw):
                continue

            comp_pos = item.get("best_position", 999)
            my_pos = my_positions.get(kw, 999)

            # Gap: they rank top 20, we rank > 50 or not at all
            if comp_pos <= 20 and my_pos > 50:
                seen.add(kw)
                gaps.append({
                    "keyword": kw,
                    "volume": item.get("volume", 0),
                    "difficulty": item.get("keyword_difficulty", 0),
                    "competitor": comp_domain,
                    "competitor_position": comp_pos,
                    "your_position": my_pos if my_pos < 999 else None,
                    "competitor_traffic": item.get("sum_traffic", 0),
                })

    gaps.sort(key=lambda x: x.get("volume", 0), reverse=True)
    return gaps


# ─────────────────────────────────────────────
# Execution tier (same as execution-pipeline)
# ─────────────────────────────────────────────

def execution_tier(kd, has_page=False):
    """Route keyword to execution tier."""
    if kd <= 20 and not has_page:
        return "Tier 1: Full Auto"
    if has_page and kd <= 50:
        return "Tier 2: Auto Refresh"
    if kd <= 40:
        return "Tier 3: Semi-Auto"
    if kd <= 60:
        return "Tier 4: Team + AI"
    return "Tier 5: Expert Only"


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def fmt_vol(v):
    if not v:
        return "—"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)


def fmt_pos(p):
    if p is None or p >= 999:
        return "not ranking"
    return f"#{p}"


def fmt_kd(k):
    if k <= 20:
        return f"KD{k} (easy)"
    if k <= 40:
        return f"KD{k} (medium)"
    if k <= 60:
        return f"KD{k} (hard)"
    return f"KD{k} (very hard)"


def main():
    output_json = "--json" in sys.argv

    # Parse CLI overrides
    competitors = COMPETITORS
    for arg in sys.argv[1:]:
        if arg.startswith("--competitors="):
            competitors = [c.strip() for c in arg.split("=", 1)[1].split(",") if c.strip()]

    print(f"🕵️  Competitor Gap Analysis — {YOUR_DOMAIN}", file=sys.stderr)
    print(f"   vs: {', '.join(competitors)}", file=sys.stderr)
    print(file=sys.stderr)

    # Pull your keywords
    print(f"📡 Fetching {YOUR_DOMAIN} organic keywords...", file=sys.stderr)
    my_keywords = fetch_organic_keywords(YOUR_DOMAIN, limit=1000)

    # Pull competitor keywords
    print("📡 Fetching competitor keywords...", file=sys.stderr)
    competitor_data = {}
    for comp in competitors:
        comp_kws = fetch_organic_keywords(comp, limit=500)
        if comp_kws:
            competitor_data[comp] = comp_kws

    if not competitor_data:
        print("  [ERROR] No competitor data fetched. Check AHREFS_TOKEN.", file=sys.stderr)
        sys.exit(1)

    # Find gaps
    print("🔍 Cross-referencing keywords...", file=sys.stderr)
    gaps = find_gaps(my_keywords, competitor_data)
    print(f"   Found {len(gaps)} gap keywords", file=sys.stderr)

    # Enrich top gaps with CPC + intent data
    print("📊 Enriching top gaps with keyword data...", file=sys.stderr)
    enriched = enrich_gaps_with_explorer(gaps)

    # Enhance gap entries with enrichment data
    for gap in gaps:
        kw = gap["keyword"]
        if kw in enriched:
            extra = enriched[kw]
            gap["cpc"] = extra.get("cpc", 0)
            gap["traffic_potential"] = extra.get("traffic_potential", 0)
            gap["intents"] = extra.get("intents", {})
        else:
            gap["cpc"] = 0
            gap["traffic_potential"] = 0
            gap["intents"] = {}

        gap["funnel"] = funnel_stage(kw, gap.get("intents"))
        gap["tier"] = execution_tier(gap["difficulty"], gap.get("your_position") is not None)

    # Save JSON
    result = {
        "generated_at": datetime.now().isoformat(),
        "your_domain": YOUR_DOMAIN,
        "competitors": competitors,
        "your_keyword_count": len(my_keywords),
        "total_gaps": len(gaps),
        "gaps": gaps[:100],  # top 100
        "summary": {
            "total_gaps": len(gaps),
            "bofu_gaps": len([g for g in gaps if g["funnel"] == "BOFU"]),
            "mofu_gaps": len([g for g in gaps if g["funnel"] == "MOFU"]),
            "tofu_gaps": len([g for g in gaps if g["funnel"] == "TOFU"]),
            "easy_gaps": len([g for g in gaps if g["difficulty"] <= 20]),
            "medium_gaps": len([g for g in gaps if 20 < g["difficulty"] <= 40]),
            "hard_gaps": len([g for g in gaps if g["difficulty"] > 40]),
            "tier1_auto": len([g for g in gaps if g["tier"] == "Tier 1: Full Auto"]),
            "by_competitor": {comp: len([g for g in gaps if g["competitor"] == comp]) for comp in competitors},
        },
    }

    json_path = OUTPUT_DIR / "competitor-gap-latest.json"
    json_path.write_text(json.dumps(result, indent=2))
    print(f"💾 Saved to {json_path}", file=sys.stderr)
    print(file=sys.stderr)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print(f"🕵️  COMPETITOR GAP ANALYSIS — {YOUR_DOMAIN}")
        print(f"   Your organic keywords: {len(my_keywords)}")
        print(f"   Competitors analyzed: {', '.join(competitors)}")
        print(f"   Total gaps found: {len(gaps)}")
        print()

        # BOFU gaps first (most valuable)
        bofu_gaps = [g for g in gaps if g["funnel"] == "BOFU"]
        if bofu_gaps:
            print("💰 BOFU GAPS (money keywords you're missing)")
            print()
            for i, gap in enumerate(bofu_gaps[:15], 1):
                cpc_str = f"${gap['cpc']/100:.2f}" if gap.get("cpc") else "—"
                print(f"  {i:>2}. {gap['keyword']}")
                print(f"       Vol: {fmt_vol(gap['volume'])}  {fmt_kd(gap['difficulty'])}  CPC: {cpc_str}")
                print(f"       {gap['competitor']} #{gap['competitor_position']}  |  You: {fmt_pos(gap.get('your_position'))}")
                print(f"       {gap['tier']}")
                print()

        # Easy gaps (Tier 1 candidates)
        easy = [g for g in gaps if g["difficulty"] <= 20]
        if easy:
            print(f"🟢 EASY GAPS — KD <= 20 ({len(easy)} keywords)")
            print()
            for i, gap in enumerate(easy[:15], 1):
                cpc_str = f"${gap['cpc']/100:.2f}" if gap.get("cpc") else "—"
                print(f"  {i:>2}. {gap['keyword']}")
                print(f"       Vol: {fmt_vol(gap['volume'])}  KD: {gap['difficulty']}  CPC: {cpc_str}  [{gap['funnel']}]")
                print(f"       {gap['competitor']} #{gap['competitor_position']}")
                print()

        # All gaps by volume (top 20)
        print(f"📊 ALL GAPS BY VOLUME (top 20 of {len(gaps)})")
        print()
        for i, gap in enumerate(gaps[:20], 1):
            cpc_str = f"${gap['cpc']/100:.2f}" if gap.get("cpc") else "—"
            print(f"  {i:>2}. {gap['keyword']}")
            print(f"       Vol: {fmt_vol(gap['volume'])}  {fmt_kd(gap['difficulty'])}  CPC: {cpc_str}  [{gap['funnel']}]")
            print(f"       {gap['competitor']} #{gap['competitor_position']}  |  You: {fmt_pos(gap.get('your_position'))}")
            print(f"       {gap['tier']}")
            print()

        # Pipeline summary
        from collections import Counter as C
        tier_counts = C(g["tier"] for g in gaps)
        print("⚡ EXECUTION PIPELINE SUMMARY")
        print()
        for tier in ["Tier 1: Full Auto", "Tier 2: Auto Refresh", "Tier 3: Semi-Auto", "Tier 4: Team + AI", "Tier 5: Expert Only"]:
            count = tier_counts.get(tier, 0)
            if count:
                print(f"   {tier}: {count} keywords")
        print()

        # Competitor breakdown
        print("📊 GAPS BY COMPETITOR")
        print()
        for comp in competitors:
            comp_gaps = [g for g in gaps if g["competitor"] == comp]
            if comp_gaps:
                avg_kd = sum(g["difficulty"] for g in comp_gaps) / len(comp_gaps)
                print(f"   {comp}: {len(comp_gaps)} gaps (avg KD: {avg_kd:.0f})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
