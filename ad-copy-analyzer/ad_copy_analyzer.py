#!/usr/bin/env python3
"""
Ad Copy Analyzer for Google Ads.

Pulls ad copy (RSA headlines + descriptions) from the Google Ads API,
scores them against direct-response copywriting principles from
"Classified Ad Secrets", and outputs a JSON report for Claude to
interpret and present suggestions.

Usage:
  python ad_copy_analyzer.py --account barker-wellness
  python ad_copy_analyzer.py --account barker-wellness --campaign-id 23575383776
  python ad_copy_analyzer.py --account barker-wellness --lookback 90
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
ENV_PATH = SCRIPT_DIR.parent.parent.parent / ".env"

# ---------------------------------------------------------------------------
# Power words from "Classified Ad Secrets"
# ---------------------------------------------------------------------------
YALE_12 = {
    "discover", "easy", "guarantee", "health", "love", "money",
    "new", "proven", "results", "safety", "save", "you", "free",
}

POWER_WORDS = {
    "absolutely", "amazing", "approved", "attractive", "authentic", "bargain",
    "beautiful", "better", "big", "colorful", "colossal", "complete",
    "confidential", "crammed", "delivered", "direct", "discount", "easily",
    "endorsed", "enormous", "excellent", "exciting", "exclusive", "expert",
    "famous", "fascinating", "fortune", "full", "genuine", "gift", "gigantic",
    "greatest", "guaranteed", "helpful", "highest", "huge", "immediately",
    "improved", "informative", "instructive", "interesting", "largest",
    "latest", "lavishly", "liberal", "lifetime", "limited", "lowest", "magic",
    "mammoth", "miracle", "noted", "odd", "outstanding", "personalized",
    "popular", "powerful", "practical", "professional", "profitable",
    "profusely", "proven", "quality", "quickly", "rare", "reduced",
    "refundable", "remarkable", "reliable", "revealing", "revolutionary",
    "scarce", "secrets", "security", "selected", "sensational", "simplified",
    "sizable", "special", "startling", "strange", "strong", "sturdy",
    "successful", "superior", "surprise", "terrific", "tested", "tremendous",
    "unconditional", "unique", "unlimited", "unparalleled", "unsurpassed",
    "unusual", "useful", "valuable", "wealth", "weird", "wonderful",
}

ACTION_PHRASES = {
    "act now", "order now", "call today", "get started", "don't delay",
    "limited time", "limited offer", "while supplies last", "rush",
    "don't miss", "send today", "shop now", "buy now", "try now",
    "get yours", "claim", "grab", "unlock", "start today", "sign up",
    "join now", "save now", "learn more", "find out", "see how",
    "get free", "request", "reserve", "secure", "apply now",
}

URGENCY_WORDS = {
    "now", "today", "hurry", "limited", "last", "ending", "final",
    "deadline", "expires", "rush", "instant", "immediately", "fast",
    "quick", "don't wait", "before", "running out", "only",
}

BENEFIT_INDICATORS = {
    "save", "get", "enjoy", "discover", "learn", "earn", "boost",
    "improve", "increase", "reduce", "eliminate", "transform", "achieve",
    "unlock", "maximize", "double", "triple", "slash", "stop", "start",
    "feel", "look", "become",
}

EMOTIONAL_TRIGGERS = {
    "fear": {"don't miss", "before it's too late", "warning", "danger",
             "risk", "avoid", "mistake", "never", "stop", "protect"},
    "greed": {"profit", "fortune", "wealth", "earn", "income", "cash",
              "money", "rich", "millionaire", "bonus", "extra"},
    "social_proof": {"proven", "trusted", "rated", "reviewed", "popular",
                     "bestselling", "thousands", "millions", "customers",
                     "people", "everyone", "recommended", "endorsed"},
    "exclusivity": {"exclusive", "secret", "confidential", "private",
                    "invitation", "selected", "members", "vip", "insider"},
    "curiosity": {"secret", "revealed", "discover", "surprising",
                  "unexpected", "strange", "weird", "shocking", "truth",
                  "hidden", "little-known", "why"},
    "ease": {"easy", "simple", "effortless", "quick", "fast", "instant",
             "automatic", "hassle-free", "no-hassle", "painless", "smooth"},
    "guarantee": {"guarantee", "guaranteed", "risk-free", "money back",
                  "refund", "no risk", "unconditional", "warranty",
                  "satisfaction", "promise"},
}

SELF_CENTERED_WORDS = {
    "we are", "we're", "our company", "we have", "we've", "we offer",
    "we provide", "our team", "we believe", "we think", "we know",
    "i am", "i'm", "my company",
}

# ---------------------------------------------------------------------------
# STEPPS framework from "Contagious" by Jonah Berger (tastemaking layer)
# ---------------------------------------------------------------------------
SOCIAL_CURRENCY_WORDS = {
    "secret", "insider", "exclusive", "members", "vip", "invitation",
    "hidden", "little-known", "rare", "first", "unlock", "revealed",
    "confidential", "private", "selected", "elite", "only",
}

REMARKABILITY_PATTERNS = [
    r'\d+x\b', r'\d+%', r'#\d+', r'vs\.?', r'myth',
    r'surprising', r'unexpected', r'counterintuitive', r'shocking',
    r'you won.t believe', r'turns out', r'actually',
]

TRIGGER_WORDS = {
    "morning", "night", "daily", "everyday", "routine", "monday",
    "friday", "weekend", "coffee", "breakfast", "lunch", "dinner",
    "bedtime", "commute", "workout", "wake", "sleep",
}

HIGH_AROUSAL_POSITIVE = {
    "amazing", "incredible", "jaw-dropping", "mind-blowing", "stunning",
    "extraordinary", "unbelievable", "phenomenal", "breathtaking",
    "game-changing", "revolutionary", "breakthrough", "wow",
    "exciting", "thrilling", "electrifying",
}

HIGH_AROUSAL_NEGATIVE = {
    "outrageous", "furious", "shocking", "disgusting", "alarming",
    "terrifying", "infuriating", "unacceptable", "ridiculous",
    "tired of", "sick of", "fed up", "stop paying", "ripped off",
    "overpaying", "scam", "waste",
}

LOW_AROUSAL_PENALTY = {
    "content", "satisfied", "relaxed", "calm", "peaceful", "gentle",
    "soothing", "comforting", "pleasant", "nice", "fine", "okay",
}

SOCIAL_PROOF_NUMBERS = re.compile(
    r'(\d[\d,]*)\+?\s*(customers?|users?|people|reviews?|ratings?|'
    r'sold|served|trust|joined|switched|love|fans|members|orders?)',
    re.IGNORECASE,
)

PRACTICAL_VALUE_SIGNALS = {
    "tips", "ways", "tricks", "hack", "hacks", "how to", "guide",
    "step", "steps", "rule", "rules", "lesson", "lessons", "checklist",
}

STORY_INDICATORS = {
    "she", "he", "they", "was", "were", "then", "after", "before",
    "finally", "turned out", "discovered", "realized", "switched",
    "tried", "skeptic", "skeptical", "changed", "transformed",
    "from", "journey",
}

DEAL_FRAME_PATTERNS = [
    r'compare at',
    r'usually \$',
    r'regularly \$',
    r'was \$\d+.*now',
    r'valued? at \$',
    r'\$\d+\s*off',
    r'\d+%\s*off',
    r'limit\s*\d+',
    r'only\s*\d+\s*left',
    r'first\s*\d+\s*(customers?|orders?)',
]

# ---------------------------------------------------------------------------
# PPC Best Practice Scoring (2025-2026)
# ---------------------------------------------------------------------------

# Title Case detection: each word starts with uppercase (except minor words)
TITLE_CASE_MINOR_WORDS = {"a", "an", "the", "and", "but", "or", "for", "nor",
                          "in", "on", "at", "to", "by", "of", "with", "vs", "via"}

def is_title_case(text):
    """Check if text is in Title Case (first letter of major words capitalized)."""
    words = text.split()
    if not words:
        return False
    # First word must be capitalized
    if not words[0][0].isupper():
        return False
    for w in words[1:]:
        # Skip minor words, numbers, symbols
        clean = re.sub(r'[^a-zA-Z]', '', w)
        if not clean:
            continue
        if clean.lower() in TITLE_CASE_MINOR_WORDS:
            continue
        if not clean[0].isupper():
            return False
    return True

# Headline diversity categories for RSA scoring
HEADLINE_CATEGORIES = {
    "keyword": [],  # filled dynamically per ad group
    "brand": {"train with dave", "twd", "dave's", "dave"},
    "benefit": BENEFIT_INDICATORS,
    "cta": {"book", "get", "start", "schedule", "call", "visit", "discover",
            "request", "claim", "try", "find"},
    "social_proof": {"voted", "award", "winning", "best", "top", "rated",
                     "#1", "trusted", "proven", "certified"},
    "offer": {"free", "consultation", "consult", "guide", "download", "trial"},
    "urgency": URGENCY_WORDS,
}

# Specific CTA phrases for descriptions (more specific = better)
SPECIFIC_CTAS = {
    "book your free consult", "schedule your free consult",
    "book free consultation", "schedule free consultation",
    "get your free consult", "start with a free consult",
    "request your free consult", "claim your free consult",
    "book your free assessment", "get a free quote",
    "see pricing", "view pricing", "compare plans",
}

# Generic CTAs to penalize
GENERIC_CTAS = {
    "click here", "learn more", "find out more", "visit us",
    "contact us", "see more", "read more",
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

    if "GOOGLE_ADS_REFRESH_TOKEN" in env:
        credentials_config["refresh_token"] = env["GOOGLE_ADS_REFRESH_TOKEN"]
    else:
        print("ERROR: No GOOGLE_ADS_REFRESH_TOKEN in .env.", file=sys.stderr)
        sys.exit(1)

    return GoogleAdsClient.load_from_dict(credentials_config)


def fetch_ad_copy(client, customer_id, lookback_days, campaign_id=None,
                  min_impressions=100, min_clicks=5):
    """Fetch RSA ad copy with performance metrics."""
    ga_service = client.get_service("GoogleAdsService")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    campaign_filter = ""
    if campaign_id:
        campaign_filter = f"AND campaign.id = {campaign_id}"

    query = f"""
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.name,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls,
            ad_group_ad.status,
            ad_group_ad.ad.type,
            ad_group.id,
            ad_group.name,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.all_conversions
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
          AND ad_group_ad.status != 'REMOVED'
          AND metrics.impressions >= {min_impressions}
          {campaign_filter}
        ORDER BY metrics.impressions DESC
    """

    results = []
    response = ga_service.search_stream(customer_id=customer_id, query=query)
    for batch in response:
        for row in batch.results:
            ad = row.ad_group_ad.ad
            headlines = [h.text for h in ad.responsive_search_ad.headlines]
            descriptions = [d.text for d in ad.responsive_search_ad.descriptions]
            final_urls = list(ad.final_urls) if ad.final_urls else []

            impressions = row.metrics.impressions
            clicks = row.metrics.clicks
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            conv_rate = (conversions / clicks * 100) if clicks > 0 else 0
            cpa = (cost / conversions) if conversions > 0 else None
            roas = (row.metrics.conversions_value / cost) if cost > 0 else None

            results.append({
                "ad_id": row.ad_group_ad.ad.id,
                "campaign_id": row.campaign.id,
                "campaign_name": row.campaign.name,
                "ad_group_id": row.ad_group.id,
                "ad_group_name": row.ad_group.name,
                "headlines": headlines,
                "descriptions": descriptions,
                "final_urls": final_urls,
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "cost": round(cost, 2),
                "conversions": round(conversions, 2),
                "conv_rate": round(conv_rate, 2),
                "cpa": round(cpa, 2) if cpa else None,
                "roas": round(roas, 2) if roas else None,
            })

    return results


def fetch_asset_details(client, customer_id, campaign_id=None):
    """Fetch image, video, and other media assets linked to ads."""
    ga_service = client.get_service("GoogleAdsService")

    campaign_filter = ""
    if campaign_id:
        campaign_filter = f"AND campaign.id = {campaign_id}"

    # Query 1: Ad-level image assets (image extensions, etc.)
    image_query = f"""
        SELECT
            asset.id,
            asset.name,
            asset.type,
            asset.image_asset.full_size.url,
            asset.image_asset.full_size.width_pixels,
            asset.image_asset.full_size.height_pixels,
            asset.image_asset.mime_type,
            asset.image_asset.file_size,
            campaign.id,
            campaign.name
        FROM campaign_asset
        WHERE asset.type = 'IMAGE'
          AND campaign_asset.status != 'REMOVED'
          {campaign_filter}
    """

    # Query 2: YouTube video assets
    video_query = f"""
        SELECT
            asset.id,
            asset.name,
            asset.type,
            asset.youtube_video_asset.youtube_video_id,
            asset.youtube_video_asset.youtube_video_title,
            campaign.id,
            campaign.name
        FROM campaign_asset
        WHERE asset.type = 'YOUTUBE_VIDEO'
          AND campaign_asset.status != 'REMOVED'
          {campaign_filter}
    """

    # Query 3: Asset group assets (Performance Max)
    pmax_query = f"""
        SELECT
            asset_group.id,
            asset_group.name,
            asset_group.status,
            asset_group_asset.asset,
            asset_group_asset.field_type,
            asset_group_asset.status,
            asset.id,
            asset.name,
            asset.type,
            asset.image_asset.full_size.url,
            asset.image_asset.full_size.width_pixels,
            asset.image_asset.full_size.height_pixels,
            asset.youtube_video_asset.youtube_video_id,
            asset.youtube_video_asset.youtube_video_title,
            asset.text_asset.text,
            campaign.id,
            campaign.name
        FROM asset_group_asset
        WHERE asset_group_asset.status != 'REMOVED'
          {campaign_filter}
    """

    assets = {
        "campaign_images": [],
        "campaign_videos": [],
        "pmax_asset_groups": defaultdict(lambda: {
            "name": "", "headlines": [], "descriptions": [],
            "long_headlines": [], "images": [], "videos": [],
            "logos": [], "campaign_name": "",
        }),
    }

    # Fetch campaign-level images
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=image_query)
        for batch in response:
            for row in batch.results:
                a = row.asset
                assets["campaign_images"].append({
                    "asset_id": a.id,
                    "name": a.name,
                    "url": a.image_asset.full_size.url if a.image_asset.full_size.url else None,
                    "width": a.image_asset.full_size.width_pixels,
                    "height": a.image_asset.full_size.height_pixels,
                    "mime_type": str(a.image_asset.mime_type) if a.image_asset.mime_type else None,
                    "file_size_bytes": a.image_asset.file_size,
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "aspect_ratio": _aspect_ratio(
                        a.image_asset.full_size.width_pixels,
                        a.image_asset.full_size.height_pixels,
                    ),
                })
    except Exception as e:
        print(f"Warning: Could not fetch campaign images: {e}", file=sys.stderr)

    # Fetch campaign-level videos
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=video_query)
        for batch in response:
            for row in batch.results:
                a = row.asset
                vid_id = a.youtube_video_asset.youtube_video_id
                assets["campaign_videos"].append({
                    "asset_id": a.id,
                    "name": a.name,
                    "youtube_video_id": vid_id,
                    "youtube_title": a.youtube_video_asset.youtube_video_title,
                    "thumbnail_url": f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else None,
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                })
    except Exception as e:
        print(f"Warning: Could not fetch campaign videos: {e}", file=sys.stderr)

    # Fetch PMax asset group assets
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=pmax_query)
        for batch in response:
            for row in batch.results:
                ag_id = row.asset_group.id
                ag = assets["pmax_asset_groups"][ag_id]
                ag["name"] = row.asset_group.name
                ag["campaign_name"] = row.campaign.name
                ag["campaign_id"] = row.campaign.id

                field = str(row.asset_group_asset.field_type)
                a = row.asset

                if "HEADLINE" in field and a.text_asset.text:
                    if "LONG" in field:
                        ag["long_headlines"].append(a.text_asset.text)
                    else:
                        ag["headlines"].append(a.text_asset.text)
                elif "DESCRIPTION" in field and a.text_asset.text:
                    ag["descriptions"].append(a.text_asset.text)
                elif "MARKETING_IMAGE" in field or "SQUARE_MARKETING_IMAGE" in field:
                    ag["images"].append({
                        "asset_id": a.id,
                        "name": a.name,
                        "url": a.image_asset.full_size.url if a.image_asset.full_size.url else None,
                        "width": a.image_asset.full_size.width_pixels,
                        "height": a.image_asset.full_size.height_pixels,
                        "field_type": field,
                        "aspect_ratio": _aspect_ratio(
                            a.image_asset.full_size.width_pixels,
                            a.image_asset.full_size.height_pixels,
                        ),
                    })
                elif "LOGO" in field:
                    ag["logos"].append({
                        "asset_id": a.id,
                        "name": a.name,
                        "url": a.image_asset.full_size.url if a.image_asset.full_size.url else None,
                        "width": a.image_asset.full_size.width_pixels,
                        "height": a.image_asset.full_size.height_pixels,
                    })
                elif "YOUTUBE_VIDEO" in field:
                    vid_id = a.youtube_video_asset.youtube_video_id
                    ag["videos"].append({
                        "asset_id": a.id,
                        "name": a.name,
                        "youtube_video_id": vid_id,
                        "youtube_title": a.youtube_video_asset.youtube_video_title,
                        "thumbnail_url": f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else None,
                    })
    except Exception as e:
        print(f"Warning: Could not fetch PMax asset groups: {e}", file=sys.stderr)

    # Convert defaultdict to regular dict for JSON
    assets["pmax_asset_groups"] = dict(assets["pmax_asset_groups"])
    return assets


def _aspect_ratio(w, h):
    """Return human-readable aspect ratio string."""
    if not w or not h:
        return None
    from math import gcd
    g = gcd(w, h)
    return f"{w // g}:{h // g}"


# ---------------------------------------------------------------------------
# Scoring Engine — based on "Classified Ad Secrets"
# ---------------------------------------------------------------------------
def tokenize(text):
    """Lowercase tokenization for word matching."""
    return set(re.findall(r'[a-z]+', text.lower()))


def score_headline(headline):
    """Score a single headline (0-100) against direct-response + PPC best practices."""
    text_lower = headline.lower()
    words = tokenize(headline)
    score = 0
    signals = []

    # 1. Power word density (up to 15 pts — reduced from 20 to make room)
    pw_count = len(words & POWER_WORDS)
    yale_count = len(words & YALE_12)
    pw_score = min(15, pw_count * 5 + yale_count * 7)
    score += pw_score
    if yale_count:
        signals.append(f"Yale-12 words: {words & YALE_12}")
    if pw_count:
        signals.append(f"{pw_count} power word(s)")

    # 2. Benefit-oriented (up to 12 pts)
    benefit_count = len(words & BENEFIT_INDICATORS)
    if benefit_count:
        score += min(12, benefit_count * 6)
        signals.append("benefit-oriented")

    # 3. Contains "you/your" (8 pts)
    if "you" in words or "your" in words:
        score += 8
        signals.append("addresses reader directly")

    # 4. Action/urgency (up to 12 pts)
    action_found = any(p in text_lower for p in ACTION_PHRASES)
    urgency_found = len(words & URGENCY_WORDS)
    if action_found:
        score += 8
        signals.append("has call-to-action")
    if urgency_found:
        score += min(4, urgency_found * 2)
        signals.append("urgency present")

    # 5. Emotional triggers (up to 10 pts)
    triggers_hit = []
    for trigger_name, trigger_words in EMOTIONAL_TRIGGERS.items():
        if words & trigger_words or any(p in text_lower for p in trigger_words):
            triggers_hit.append(trigger_name)
    if triggers_hit:
        score += min(10, len(triggers_hit) * 4)
        signals.append(f"emotional triggers: {triggers_hit}")

    # 6. Specificity — numbers, percentages (8 pts)
    if re.search(r'\d', headline):
        score += 8
        signals.append("contains specific numbers")

    # 7. Length check — headlines should be concise but fill space (up to 8 pts)
    char_len = len(headline)
    if 20 <= char_len <= 30:
        score += 8
        signals.append("optimal length (fills space)")
    elif 15 <= char_len <= 30:
        score += 5
        signals.append("good length")
    elif char_len < 15:
        signals.append("MISSING: headline too short (under 15 chars)")

    # 8. Title Case check (7 pts) — PPC best practice
    if is_title_case(headline):
        score += 7
        signals.append("proper Title Case")
    else:
        signals.append("MISSING: not Title Case")

    # 9. Character utilization bonus (5 pts) — using 25-30 of 30 chars
    if 25 <= char_len <= 30:
        score += 5
        signals.append("max char utilization")

    # 10. Penalty: self-centered language (-10 pts)
    if any(sc in text_lower for sc in SELF_CENTERED_WORDS):
        score -= 10
        signals.append("PENALTY: self-centered (uses we/our/I)")

    # 11. Penalty: all caps (-5 pts)
    if headline == headline.upper() and len(headline) > 5:
        score -= 5
        signals.append("PENALTY: all caps")

    # 12. Penalty: generic/vague (-5 pts)
    generic_phrases = {"click here", "learn more", "find out more", "visit us"}
    if any(g in text_lower for g in generic_phrases):
        score -= 5
        signals.append("PENALTY: generic headline")

    return {
        "text": headline,
        "score": max(0, min(100, score)),
        "signals": signals,
    }


def score_description(description):
    """Score a single description (0-100) against direct-response + PPC best practices."""
    text_lower = description.lower()
    words = tokenize(description)
    score = 0
    signals = []

    # 1. Power word density (up to 12 pts)
    pw_count = len(words & POWER_WORDS)
    yale_count = len(words & YALE_12)
    pw_score = min(12, pw_count * 3 + yale_count * 5)
    score += pw_score
    if pw_count or yale_count:
        signals.append(f"{pw_count + yale_count} power/Yale words")

    # 2. Benefit-oriented (up to 15 pts) — descriptions should sell benefits
    benefit_count = len(words & BENEFIT_INDICATORS)
    if benefit_count:
        score += min(15, benefit_count * 6)
        signals.append(f"benefit-focused ({benefit_count} indicators)")

    # 3. "You/your" usage (8 pts)
    if "you" in words or "your" in words:
        score += 8
        signals.append("reader-focused")

    # 4. Call-to-action quality (up to 15 pts)
    specific_cta = any(p in text_lower for p in SPECIFIC_CTAS)
    generic_cta = any(p in text_lower for p in GENERIC_CTAS)
    basic_cta = any(p in text_lower for p in ACTION_PHRASES)
    if specific_cta:
        score += 15
        signals.append("specific CTA (best practice)")
    elif basic_cta and not generic_cta:
        score += 10
        signals.append("good CTA")
    elif generic_cta:
        score += 3
        signals.append("MISSING: generic CTA (use specific CTAs like 'Book Your Free Consult')")
    else:
        signals.append("MISSING: no call-to-action")

    # 5. Emotional triggers (up to 10 pts)
    triggers_hit = []
    for trigger_name, trigger_words in EMOTIONAL_TRIGGERS.items():
        if words & trigger_words or any(p in text_lower for p in trigger_words):
            triggers_hit.append(trigger_name)
    if triggers_hit:
        score += min(10, len(triggers_hit) * 4)
        signals.append(f"emotional triggers: {triggers_hit}")

    # 6. Guarantee/risk reversal (8 pts)
    guarantee_words = EMOTIONAL_TRIGGERS["guarantee"]
    if words & guarantee_words or any(p in text_lower for p in guarantee_words):
        score += 8
        signals.append("includes guarantee/risk reversal")

    # 7. Specificity (5 pts)
    if re.search(r'\d', description):
        score += 5
        signals.append("specific numbers")

    # 8. Length — descriptions should maximize space (up to 10 pts)
    char_len = len(description)
    if 75 <= char_len <= 90:
        score += 10
        signals.append("optimal length (maximizes space)")
    elif 60 <= char_len <= 90:
        score += 7
        signals.append("good length")
    elif 45 <= char_len <= 60:
        score += 3
        signals.append("MISSING: description too short (aim for 75-90 chars)")

    # 9. Unique value proposition check (7 pts)
    uvp_words = {"only", "exclusive", "unique", "unlike", "first", "best",
                 "award", "voted", "certified", "degreed", "kinesiology"}
    if words & uvp_words:
        score += 7
        signals.append("unique differentiator present")

    # 10. Distinct message check — penalize if description just restates headline-like content
    # (This is checked at ad level, not here)

    # 11. Penalty: self-centered (-10 pts)
    if any(sc in text_lower for sc in SELF_CENTERED_WORDS):
        score -= 10
        signals.append("PENALTY: self-centered")

    # 12. Penalty: generic CTA (-3 pts)
    if generic_cta and not specific_cta:
        score -= 3
        signals.append("PENALTY: generic CTA")

    return {
        "text": description,
        "score": max(0, min(100, score)),
        "signals": signals,
    }


def score_stepps(text):
    """Score a text block (headline or description) on STEPPS tastemaking (0-100)."""
    text_lower = text.lower()
    words = tokenize(text)
    score = 0
    signals = []

    # 1. Social Currency (up to 20 pts)
    sc_count = len(words & SOCIAL_CURRENCY_WORDS)
    remark_count = sum(1 for p in REMARKABILITY_PATTERNS if re.search(p, text_lower))
    sc_score = min(20, sc_count * 5 + remark_count * 7)
    if sc_count or remark_count:
        score += sc_score
        signals.append(f"social currency ({sc_count} insider + {remark_count} remarkable)")

    # 2. Triggers — linked to daily cues (up to 15 pts)
    trigger_count = len(words & TRIGGER_WORDS)
    if trigger_count:
        score += min(15, trigger_count * 8)
        signals.append(f"trigger ({trigger_count} daily cue words)")

    # 3. Emotion — high arousal (up to 25 pts), penalize low arousal
    hi_pos = len(words & HIGH_AROUSAL_POSITIVE) + sum(
        1 for p in HIGH_AROUSAL_POSITIVE if len(p.split()) > 1 and p in text_lower)
    hi_neg = len(words & HIGH_AROUSAL_NEGATIVE) + sum(
        1 for p in HIGH_AROUSAL_NEGATIVE if len(p.split()) > 1 and p in text_lower)
    lo_count = len(words & LOW_AROUSAL_PENALTY)
    if hi_pos:
        score += min(15, hi_pos * 8)
        signals.append(f"high-arousal positive (awe/excitement)")
    if hi_neg:
        score += min(10, hi_neg * 6)
        signals.append(f"high-arousal negative (anger/anxiety)")
    if lo_count:
        score -= min(10, lo_count * 5)
        signals.append(f"PENALTY: low-arousal emotion ({lo_count} words)")

    # 4. Public / Social Proof (up to 15 pts)
    sp_match = SOCIAL_PROOF_NUMBERS.search(text)
    if sp_match:
        score += 15
        signals.append(f"social proof: '{sp_match.group()}'")
    elif words & {"join", "joined", "trusted", "rated", "reviewed"}:
        score += 7
        signals.append("social proof (soft)")

    # 5. Practical Value (up to 15 pts)
    pv_count = sum(1 for p in DEAL_FRAME_PATTERNS if re.search(p, text_lower))
    pv_words = len(words & PRACTICAL_VALUE_SIGNALS)
    if pv_count:
        score += min(10, pv_count * 5)
        signals.append(f"deal framing ({pv_count} techniques)")
    if pv_words:
        score += min(5, pv_words * 3)
        signals.append(f"practical value (useful info)")

    # 6. Story / Narrative (up to 10 pts)
    story_count = len(words & STORY_INDICATORS)
    if story_count >= 2:
        score += min(10, story_count * 3)
        signals.append(f"narrative elements ({story_count} story words)")

    return {
        "score": max(0, min(100, score)),
        "signals": signals,
    }


def score_ppc_structure(ad):
    """Score PPC-specific structural best practices (0-100). Separate from copy quality."""
    score = 0
    signals = []
    headlines = ad.get("headlines", [])
    descriptions = ad.get("descriptions", [])

    # 1. Headline count (up to 15 pts) — Google recommends all 15 slots
    h_count = len(headlines)
    if h_count >= 15:
        score += 15
        signals.append("all 15 headline slots used")
    elif h_count >= 10:
        score += 10
        signals.append(f"MISSING: only {h_count}/15 headlines (aim for 15)")
    elif h_count >= 5:
        score += 5
        signals.append(f"MISSING: only {h_count}/15 headlines (severely limiting optimization)")
    else:
        signals.append(f"MISSING: only {h_count}/15 headlines (critically low)")

    # 2. Description count (up to 10 pts) — Google recommends all 4 slots
    d_count = len(descriptions)
    if d_count >= 4:
        score += 10
        signals.append("all 4 description slots used")
    elif d_count >= 2:
        score += 5
        signals.append(f"MISSING: only {d_count}/4 descriptions (aim for 4)")
    else:
        signals.append(f"MISSING: only {d_count}/4 descriptions (critically low)")

    # 3. Display paths (15 pts) — path1 and path2 should be set
    path1 = ad.get("path1", "")
    path2 = ad.get("path2", "")
    if path1 and path2:
        score += 15
        signals.append(f"display paths set: /{path1}/{path2}")
    elif path1:
        score += 8
        signals.append(f"MISSING: only Path 1 set (add Path 2 for keyword reinforcement)")
    else:
        signals.append("MISSING: no display paths (free keyword/relevance real estate wasted)")

    # 4. Headline diversity (up to 20 pts) — headlines should cover different categories
    h_lower = [h.lower() for h in headlines]
    all_h_text = " ".join(h_lower)
    categories_found = set()
    # Check for keyword/service mentions
    if any(w in all_h_text for w in ["personal train", "trainer", "training"]):
        categories_found.add("keyword")
    # Brand
    if any(w in all_h_text for w in HEADLINE_CATEGORIES["brand"]):
        categories_found.add("brand")
    # Benefit
    h_words = tokenize(" ".join(headlines))
    if h_words & HEADLINE_CATEGORIES["benefit"]:
        categories_found.add("benefit")
    # CTA
    if h_words & HEADLINE_CATEGORIES["cta"]:
        categories_found.add("cta")
    # Social proof
    if h_words & HEADLINE_CATEGORIES["social_proof"]:
        categories_found.add("social_proof")
    # Offer
    if h_words & HEADLINE_CATEGORIES["offer"]:
        categories_found.add("offer")
    # Urgency
    if h_words & HEADLINE_CATEGORIES["urgency"]:
        categories_found.add("urgency")

    diversity_score = min(20, len(categories_found) * 3)
    score += diversity_score
    if len(categories_found) >= 5:
        signals.append(f"good headline diversity ({len(categories_found)}/7 categories)")
    else:
        missing_cats = {"keyword", "brand", "benefit", "cta", "social_proof", "offer", "urgency"} - categories_found
        signals.append(f"MISSING: headline diversity low ({len(categories_found)}/7) — add: {', '.join(missing_cats)}")

    # 5. Headline uniqueness (up to 10 pts) — no near-duplicate headlines
    unique_count = len(set(h_lower))
    dup_count = len(h_lower) - unique_count
    if dup_count == 0:
        score += 10
        signals.append("all headlines unique")
    else:
        score += max(0, 10 - dup_count * 3)
        signals.append(f"PENALTY: {dup_count} duplicate headline(s)")

    # 6. Description distinctness (up to 10 pts) — each description should say something different
    d_lower = [d.lower() for d in descriptions]
    unique_d = len(set(d_lower))
    if unique_d == d_count and d_count >= 2:
        score += 10
        signals.append("all descriptions distinct")
    elif d_count > 0:
        score += 5

    # 7. Title Case consistency across headlines (up to 10 pts)
    tc_count = sum(1 for h in headlines if is_title_case(h))
    tc_pct = tc_count / max(1, h_count)
    if tc_pct >= 0.9:
        score += 10
        signals.append("consistent Title Case across headlines")
    elif tc_pct >= 0.6:
        score += 5
        signals.append(f"MISSING: only {tc_count}/{h_count} headlines in Title Case")
    else:
        signals.append(f"MISSING: poor Title Case ({tc_count}/{h_count} headlines)")

    # 8. CTA in multiple descriptions (up to 10 pts)
    cta_descs = sum(1 for d in descriptions if any(p in d.lower() for p in ACTION_PHRASES | SPECIFIC_CTAS))
    if cta_descs >= 2:
        score += 10
        signals.append(f"CTA in {cta_descs} descriptions")
    elif cta_descs == 1:
        score += 5
        signals.append("MISSING: CTA in only 1 description (aim for 2+)")
    else:
        signals.append("MISSING: no CTA in any description")

    return {
        "score": max(0, min(100, score)),
        "signals": signals,
    }


def score_ad(ad):
    """Score an entire RSA ad. Returns enriched ad dict with scores."""
    headline_scores = [score_headline(h) for h in ad["headlines"]]
    description_scores = [score_description(d) for d in ad["descriptions"]]

    avg_headline = (sum(h["score"] for h in headline_scores) / len(headline_scores)
                    if headline_scores else 0)
    avg_description = (sum(d["score"] for d in description_scores) / len(description_scores)
                       if description_scores else 0)

    # DR score: 50% headline, 50% description
    dr_score = round(avg_headline * 0.5 + avg_description * 0.5, 1)

    # STEPPS tastemaking score (across full ad text)
    all_text = " ".join(ad["headlines"] + ad["descriptions"])
    stepps_result = score_stepps(all_text)
    stepps_score = stepps_result["score"]
    stepps_signals = stepps_result["signals"]

    # PPC structural best practices score
    ppc_result = score_ppc_structure(ad)
    ppc_score = ppc_result["score"]
    ppc_signals = ppc_result["signals"]

    # New blend: 50% DR copy + 10% STEPPS + 40% PPC structure
    overall = round(dr_score * 0.50 + stepps_score * 0.10 + ppc_score * 0.40, 1)

    # AIDA completeness check
    all_lower = all_text.lower()
    all_words = tokenize(all_text)
    aida = {
        "attention": bool(all_words & POWER_WORDS or all_words & YALE_12),
        "interest": bool(all_words & BENEFIT_INDICATORS),
        "desire": bool(any(
            all_words & tw or any(p in all_lower for p in tw)
            for tw in EMOTIONAL_TRIGGERS.values()
        )),
        "action": bool(any(p in all_lower for p in ACTION_PHRASES)),
    }
    aida_score = sum(aida.values())
    aida_missing = [k.upper() for k, v in aida.items() if not v]

    # STEPPS completeness check
    stepps_elements = {
        "social_currency": bool(all_words & SOCIAL_CURRENCY_WORDS or
                                any(re.search(p, all_lower) for p in REMARKABILITY_PATTERNS)),
        "triggers": bool(all_words & TRIGGER_WORDS),
        "emotion": bool(all_words & HIGH_AROUSAL_POSITIVE or all_words & HIGH_AROUSAL_NEGATIVE),
        "public": bool(SOCIAL_PROOF_NUMBERS.search(all_text) or
                       all_words & {"join", "trusted", "rated"}),
        "practical_value": bool(any(re.search(p, all_lower) for p in DEAL_FRAME_PATTERNS) or
                                all_words & PRACTICAL_VALUE_SIGNALS),
        "stories": bool(len(all_words & STORY_INDICATORS) >= 2),
    }
    stepps_count = sum(stepps_elements.values())
    stepps_missing = [k.upper() for k, v in stepps_elements.items() if not v]

    # Collect all unique signals
    weaknesses = []
    strengths = []
    for item in headline_scores + description_scores:
        for s in item["signals"]:
            if s.startswith("PENALTY") or s.startswith("MISSING"):
                if s not in weaknesses:
                    weaknesses.append(s)
            else:
                if s not in strengths:
                    strengths.append(s)
    for s in stepps_signals + ppc_signals:
        if s.startswith("PENALTY") or s.startswith("MISSING"):
            if s not in weaknesses:
                weaknesses.append(s)
        else:
            if s not in strengths:
                strengths.append(s)

    return {
        **ad,
        "headline_scores": headline_scores,
        "description_scores": description_scores,
        "avg_headline_score": round(avg_headline, 1),
        "avg_description_score": round(avg_description, 1),
        "dr_score": dr_score,
        "stepps_score": stepps_score,
        "stepps_signals": stepps_signals,
        "stepps_elements": stepps_elements,
        "stepps_count": f"{stepps_count}/6",
        "stepps_missing": stepps_missing,
        "ppc_score": ppc_score,
        "ppc_signals": ppc_signals,
        "overall_copy_score": overall,
        "aida": aida,
        "aida_score": f"{aida_score}/4",
        "aida_missing": aida_missing,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Ad Copy Analyzer")
    parser.add_argument("--account", required=True,
                        help="Account key from config (e.g. barker-wellness)")
    parser.add_argument("--campaign-id", type=int, default=None,
                        help="Optional: analyze only this campaign")
    parser.add_argument("--lookback", type=int, default=None,
                        help="Lookback days (default from config)")
    parser.add_argument("--top", type=int, default=None,
                        help="Number of ads to return (default from config)")
    parser.add_argument("--min-impressions", type=int, default=None)
    parser.add_argument("--min-clicks", type=int, default=None)
    args = parser.parse_args()

    config = load_config()
    env = load_env()

    if args.account not in config["accounts"]:
        print(f"ERROR: Unknown account '{args.account}'. "
              f"Available: {list(config['accounts'].keys())}", file=sys.stderr)
        sys.exit(1)

    account = config["accounts"][args.account]
    customer_id = account["customer_id"]
    lookback = args.lookback or config.get("lookback_days", 90)
    top_n = args.top or config.get("top_n_ads", 20)
    min_imp = args.min_impressions or config.get("min_impressions", 100)
    min_clk = args.min_clicks or config.get("min_clicks", 5)

    print(f"Fetching ad copy for {account['label']} "
          f"(last {lookback} days)...", file=sys.stderr)

    client = get_google_ads_client(env, config)
    ads = fetch_ad_copy(client, customer_id, lookback,
                        campaign_id=args.campaign_id,
                        min_impressions=min_imp, min_clicks=min_clk)

    print(f"Fetching visual assets...", file=sys.stderr)
    assets = fetch_asset_details(client, customer_id,
                                 campaign_id=args.campaign_id)

    if not ads and not assets["pmax_asset_groups"]:
        print(json.dumps({"error": "No ads found matching criteria",
                           "account": account["label"]}))
        sys.exit(0)

    print(f"Found {len(ads)} RSA ads, "
          f"{len(assets['campaign_images'])} image assets, "
          f"{len(assets['campaign_videos'])} video assets, "
          f"{len(assets['pmax_asset_groups'])} PMax asset groups. "
          f"Scoring...", file=sys.stderr)

    scored = [score_ad(ad) for ad in ads]
    scored.sort(key=lambda x: x["overall_copy_score"])

    # Score PMax asset group copy the same way
    pmax_scored = {}
    for ag_id, ag in assets["pmax_asset_groups"].items():
        if ag["headlines"] or ag["descriptions"]:
            pseudo_ad = {
                "headlines": ag["headlines"] + ag.get("long_headlines", []),
                "descriptions": ag["descriptions"],
            }
            ag_scores = score_ad({**pseudo_ad,
                                  "ad_id": ag_id,
                                  "campaign_id": ag.get("campaign_id"),
                                  "campaign_name": ag.get("campaign_name", ""),
                                  "ad_group_id": None,
                                  "ad_group_name": ag["name"],
                                  "final_urls": [],
                                  "impressions": 0, "clicks": 0, "ctr": 0,
                                  "cost": 0, "conversions": 0, "conv_rate": 0,
                                  "cpa": None, "roas": None})
            pmax_scored[str(ag_id)] = {
                "name": ag["name"],
                "campaign_name": ag.get("campaign_name", ""),
                "copy_scores": {
                    "headline_scores": ag_scores["headline_scores"],
                    "description_scores": ag_scores["description_scores"],
                    "avg_headline_score": ag_scores["avg_headline_score"],
                    "avg_description_score": ag_scores["avg_description_score"],
                    "overall_copy_score": ag_scores["overall_copy_score"],
                    "aida": ag_scores["aida"],
                    "aida_score": ag_scores["aida_score"],
                    "aida_missing": ag_scores["aida_missing"],
                    "strengths": ag_scores["strengths"],
                    "weaknesses": ag_scores["weaknesses"],
                },
                "images": ag["images"],
                "logos": ag["logos"],
                "videos": ag["videos"],
                "long_headlines": ag.get("long_headlines", []),
            }

    # Return top N (worst-scoring first so Claude focuses on improvements)
    output = {
        "account": account["label"],
        "customer_id": customer_id,
        "lookback_days": lookback,
        "total_ads_found": len(scored),
        "returned": min(top_n, len(scored)),
        "analysis_date": datetime.now().isoformat(),
        "ads": scored[:top_n],
        "visual_assets": {
            "campaign_images": assets["campaign_images"],
            "campaign_videos": assets["campaign_videos"],
            "pmax_asset_groups": pmax_scored,
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
