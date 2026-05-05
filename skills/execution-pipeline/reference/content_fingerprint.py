#!/usr/bin/env python3
"""
Content Fingerprint — Scan published blog content to derive keyword seeds.

Pulls all published posts from the WordPress REST API, analyzes topic
frequencies, and outputs weighted keyword seeds for the execution pipeline.

Usage:
    python content_fingerprint.py
    python content_fingerprint.py --domain jetfuel.agency
    python content_fingerprint.py --json  # Output JSON instead of table

Environment variables:
    WP_DOMAIN    — WordPress domain (default: jetfuel.agency)
    WP_USER      — WordPress username (optional, for auth)
    WP_APP_PASS  — WordPress application password (optional)
    OUTPUT_DIR   — Where to save output (default: ./output)
"""

import json
import os
import re
import sys
import urllib.request
from collections import Counter
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

WP_DOMAIN = os.environ.get("WP_DOMAIN", "jetfuel.agency")
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASS = os.environ.get("WP_APP_PASS", "")

STOPWORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall",
    "and","but","or","nor","for","yet","so","at","by","in","of","on","to",
    "with","as","that","this","these","those","it","its","i","we","you","they",
    "he","she","him","her","our","their","your","my","what","which","who","when",
    "where","how","not","all","also","more","very","just","from","about","into",
    "than","then","there","up","out","if","no","can","one","time","like",
    "get","got","use","used","make","made","work","well","way","new","good",
    "go","going","know","think","want","need","see","look","come","give",
    "take","say","even","most","much","such","here","now","over","any","some",
    "them","us","first","two","other","his","her","its","been","being",
}

# ─────────────────────────────────────────────
# Topic keywords — customized for Jetfuel's niches
# ─────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "PPC / Paid Media": [
        "ppc", "paid media", "google ads", "meta ads", "facebook ads",
        "paid search", "paid social", "roas", "cpa", "cpc", "ad creative",
        "media buying", "campaign", "retargeting", "remarketing", "display ads",
        "shopping ads", "performance max", "pmax", "broad match",
    ],
    "SEO / Organic": [
        "seo", "organic", "keyword", "ranking", "serp", "backlink",
        "technical seo", "on-page", "off-page", "search console", "gsc",
        "core web vitals", "page speed", "indexing", "crawl",
    ],
    "AI / AEO": [
        "ai", "artificial intelligence", "aeo", "answer engine",
        "llm", "chatgpt", "claude", "generative", "ai search",
        "ai marketing", "ai agents", "ai seo", "ai content",
    ],
    "CPG / Food & Beverage": [
        "cpg", "consumer packaged goods", "food brand", "beverage",
        "grocery", "retail media", "shelf velocity", "slotting",
        "kroger", "walmart", "target", "whole foods", "natural products",
        "expo west", "trade promotion", "retail distribution",
    ],
    "Health & Wellness": [
        "supplement", "wellness", "health brand", "nutraceutical",
        "probiotic", "vitamin", "functional food", "gummy", "gummies",
        "clinical", "fda", "ftc", "health claims", "medical device",
    ],
    "Beauty & Personal Care": [
        "beauty", "skincare", "cosmetics", "clean beauty", "dermatologist",
        "press-on nails", "haircare", "sephora", "ulta", "beauty brand",
    ],
    "DTC / Ecommerce": [
        "dtc", "direct to consumer", "ecommerce", "e-commerce", "shopify",
        "amazon", "conversion rate", "aov", "average order value",
        "subscription", "bundle", "landing page", "checkout",
    ],
    "Email / SMS / CRM": [
        "email marketing", "klaviyo", "sms", "email", "crm",
        "segmentation", "automation", "lifecycle", "retention",
        "abandoned cart", "welcome series", "winback",
    ],
    "Content Marketing": [
        "content marketing", "blog", "content strategy", "copywriting",
        "thought leadership", "case study", "whitepaper", "content",
    ],
    "Social Media": [
        "social media", "instagram", "tiktok", "linkedin", "youtube",
        "influencer", "ugc", "user generated", "social commerce",
        "tiktok shop", "reels", "creator",
    ],
    "Analytics / Attribution": [
        "analytics", "ga4", "google analytics", "attribution",
        "tracking", "pixel", "server-side", "conversion tracking",
        "triple whale", "northbeam", "data",
    ],
    "Agency / Services": [
        "agency", "marketing agency", "digital agency", "services",
        "client", "account management", "strategy", "consulting",
    ],
}

# Map topics to Ahrefs keyword seeds
TOPIC_TO_SEEDS = {
    "PPC / Paid Media": [
        "ppc agency", "paid media agency", "google ads agency",
        "meta ads agency", "facebook ads management", "ecommerce ppc agency",
        "paid social agency", "roas optimization", "media buying agency",
        "performance marketing agency", "google ads for ecommerce",
        "meta ads for cpg", "paid media for food brands",
    ],
    "SEO / Organic": [
        "seo agency", "ecommerce seo agency", "technical seo services",
        "seo for cpg brands", "seo content strategy",
        "enterprise seo agency", "local seo agency",
    ],
    "AI / AEO": [
        "ai marketing agency", "ai seo", "answer engine optimization",
        "aeo agency", "ai content marketing", "llm optimization",
        "generative engine optimization", "ai search optimization",
    ],
    "CPG / Food & Beverage": [
        "cpg marketing agency", "food brand marketing agency",
        "beverage marketing agency", "cpg digital marketing",
        "food and beverage ecommerce", "retail media agency",
        "cpg ecommerce agency", "natural products marketing",
        "food brand ecommerce", "beverage ecommerce strategy",
        "cpg paid media", "grocery ecommerce marketing",
    ],
    "Health & Wellness": [
        "health and wellness marketing agency", "supplement marketing agency",
        "wellness brand marketing", "nutraceutical marketing agency",
        "health brand ecommerce", "supplement ecommerce marketing",
        "wellness dtc marketing", "health cpg digital marketing",
    ],
    "Beauty & Personal Care": [
        "beauty marketing agency", "skincare marketing agency",
        "beauty brand ecommerce", "clean beauty marketing",
        "beauty dtc agency", "cosmetics digital marketing",
    ],
    "DTC / Ecommerce": [
        "dtc marketing agency", "ecommerce marketing agency",
        "shopify marketing agency", "amazon marketing agency",
        "ecommerce growth agency", "dtc growth agency",
        "conversion rate optimization agency", "ecommerce cro",
    ],
    "Email / SMS / CRM": [
        "email marketing agency", "klaviyo agency", "sms marketing agency",
        "email marketing for ecommerce", "lifecycle marketing agency",
        "retention marketing agency",
    ],
    "Content Marketing": [
        "content marketing agency", "b2b content marketing",
        "content strategy agency", "blog writing services",
    ],
    "Social Media": [
        "social media marketing agency", "influencer marketing agency",
        "tiktok marketing agency", "instagram marketing agency",
        "social commerce agency", "ugc agency",
    ],
    "Analytics / Attribution": [
        "marketing analytics agency", "attribution consulting",
        "ga4 setup services", "conversion tracking agency",
    ],
    "Agency / Services": [
        "digital marketing agency", "performance marketing agency",
        "best marketing agencies", "marketing agency pricing",
        "hire marketing agency", "marketing agency los angeles",
    ],
}


# ─────────────────────────────────────────────
# WordPress API
# ─────────────────────────────────────────────

def fetch_all_posts():
    """Pull all published posts from WordPress REST API."""
    posts = []
    page = 1
    per_page = 100

    while True:
        url = (
            f"https://{WP_DOMAIN}/wp-json/wp/v2/posts"
            f"?per_page={per_page}&page={page}&status=publish"
            f"&_fields=id,title,slug,excerpt,date,modified,link,content"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "ContentFingerprint/1.0"})

        if WP_USER and WP_APP_PASS:
            import base64
            credentials = base64.b64encode(f"{WP_USER}:{WP_APP_PASS}".encode()).decode()
            req.add_header("Authorization", f"Basic {credentials}")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                total_pages = int(response.headers.get("X-WP-TotalPages", 1))

            if not data:
                break

            posts.extend(data)
            print(f"  Fetched page {page}/{total_pages} ({len(data)} posts)", file=sys.stderr)

            if page >= total_pages:
                break
            page += 1

        except urllib.error.HTTPError as e:
            if e.code == 400:
                break
            print(f"  [WARN] WordPress API error: {e}", file=sys.stderr)
            break
        except Exception as e:
            print(f"  [WARN] WordPress fetch error: {e}", file=sys.stderr)
            break

    return posts


def strip_html(html):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ─────────────────────────────────────────────
# Fingerprinting
# ─────────────────────────────────────────────

def fingerprint_posts(posts):
    """Analyze posts for topic frequencies and phrase patterns."""
    topic_counts = Counter()
    phrase_counts = Counter()
    post_topics = []  # per-post topic breakdown

    for post in posts:
        title = strip_html(post.get("title", {}).get("rendered", ""))
        excerpt = strip_html(post.get("excerpt", {}).get("rendered", ""))
        content = strip_html(post.get("content", {}).get("rendered", ""))
        slug = post.get("slug", "")

        text = f"{title} {title} {excerpt} {slug} {content}".lower()  # title weighted 2x

        post_topic_hits = Counter()
        for topic, keywords in TOPIC_KEYWORDS.items():
            for kw in keywords:
                count = text.count(kw)
                if count > 0:
                    topic_counts[topic] += count
                    post_topic_hits[topic] += count

        # Phrase frequency (bigrams from title + excerpt only -- content is too noisy)
        short_text = f"{title} {excerpt}".lower()
        words = re.findall(r'\b[a-z][a-z\-]{2,}\b', short_text)
        words = [w for w in words if w not in STOPWORDS and len(w) > 3]
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            phrase_counts[bigram] += 1

        primary_topic = post_topic_hits.most_common(1)[0][0] if post_topic_hits else "Uncategorized"
        post_topics.append({
            "title": title,
            "slug": slug,
            "date": post.get("date", "")[:10],
            "primary_topic": primary_topic,
            "topics": dict(post_topic_hits.most_common(3)),
        })

    return topic_counts, phrase_counts, post_topics


def derive_seeds(topic_counts):
    """Return ranked keyword seeds weighted by topic frequency."""
    seeds = []
    seen = set()

    for topic, _ in topic_counts.most_common():
        for seed in TOPIC_TO_SEEDS.get(topic, []):
            if seed not in seen:
                seeds.append({"seed": seed, "source_topic": topic})
                seen.add(seed)

    # Fallback seeds (always include core terms)
    fallbacks = [
        "digital marketing agency", "ecommerce marketing agency",
        "cpg marketing agency", "performance marketing agency",
    ]
    for s in fallbacks:
        if s not in seen:
            seeds.append({"seed": s, "source_topic": "Fallback"})
            seen.add(s)

    return seeds[:150]


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def main():
    output_json = "--json" in sys.argv

    domain = WP_DOMAIN
    for arg in sys.argv[1:]:
        if arg.startswith("--domain="):
            domain = arg.split("=", 1)[1]

    print(f"📝 Content Fingerprint — {domain}", file=sys.stderr)
    print(file=sys.stderr)

    # Fetch posts
    print("📡 Fetching published posts...", file=sys.stderr)
    posts = fetch_all_posts()
    print(f"   {len(posts)} posts fetched", file=sys.stderr)

    if not posts:
        print("   [ERROR] No posts found. Check domain and API access.", file=sys.stderr)
        sys.exit(1)

    # Fingerprint
    print("🧬 Analyzing topic frequencies...", file=sys.stderr)
    topic_counts, phrase_counts, post_topics = fingerprint_posts(posts)

    # Derive seeds
    seeds = derive_seeds(topic_counts)
    print(f"   Derived {len(seeds)} keyword seeds", file=sys.stderr)
    print(file=sys.stderr)

    # Output
    result = {
        "generated_at": datetime.now().isoformat(),
        "domain": domain,
        "total_posts": len(posts),
        "topic_fingerprint": dict(topic_counts.most_common(20)),
        "top_phrases": dict(phrase_counts.most_common(30)),
        "keyword_seeds": seeds,
        "post_topics": post_topics,
    }

    # Save JSON
    json_path = OUTPUT_DIR / "content-fingerprint-latest.json"
    json_path.write_text(json.dumps(result, indent=2))
    print(f"💾 Saved to {json_path}", file=sys.stderr)

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        # Print human-readable table
        print(f"📝 CONTENT FINGERPRINT — {domain}")
        print(f"   {len(posts)} published posts analyzed")
        print()

        print("🧬 TOPIC DISTRIBUTION")
        print()
        if topic_counts:
            max_count = max(topic_counts.values())
            for topic, count in topic_counts.most_common(15):
                bar_len = max(1, int(count / max_count * 30))
                bar = "█" * bar_len
                seed_count = len(TOPIC_TO_SEEDS.get(topic, []))
                print(f"   {topic:<28} {bar} {count:>5}  ({seed_count} seeds)")
        print()

        print("📊 TOP PHRASES (title + excerpt)")
        print()
        for phrase, count in phrase_counts.most_common(15):
            print(f"   {phrase:<35} {count:>3}")
        print()

        print(f"🔑 KEYWORD SEEDS: {len(seeds)} derived")
        print(f"   Top topics driving seeds: {', '.join(t for t, _ in topic_counts.most_common(5))}")
        print()

        # Recent post breakdown
        recent = [p for p in post_topics if p["date"] >= (date.today() - timedelta(days=90)).isoformat()]
        if recent:
            print(f"📅 RECENT POSTS (last 90 days): {len(recent)}")
            topic_dist = Counter(p["primary_topic"] for p in recent)
            for topic, count in topic_dist.most_common(5):
                print(f"   {topic}: {count} posts")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
