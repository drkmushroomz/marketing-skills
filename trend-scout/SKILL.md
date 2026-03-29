---
name: trend-scout
description: "Scan multiple sources for trending topics relevant to your niches and suggest content angles. Use when the user wants to find trending topics, spot emerging content opportunities, monitor what's hot in their industry, or get ahead of trends. Also use when the user mentions 'trending,' 'what's hot,' 'emerging topics,' 'trend detection,' 'content ideas from trends,' 'Reddit trends,' 'Hacker News,' 'Google Trends,' or 'what should we write about this week.'"
metadata:
  version: 1.0.0
---

# Trend Scout

Multi-source trend detection for Jetfuel's target niches. Scans Reddit, Hacker News, Google Trends, and optionally X/Twitter for trending topics, scores them for relevance, and suggests content angles.

Inspired by Eric Siu's trend_scout.py architecture, adapted for Jetfuel's MCP-based workflow.

## Prerequisites

- `.env` with `AHREFS_TOKEN` (optional, for keyword validation)
- `.env` with `BRAVE_API_KEY` (optional, for X/Twitter trends)

## Niche Configuration

Default niches and their relevance keywords:

```
CPG / Food & Beverage:
  HIGH (25pts): cpg, consumer packaged goods, shelf velocity, retail media, grocery, slotting,
                kroger, walmart connect, roundel, trade promotion, food brand, beverage brand
  MED (10pts):  dtc, direct to consumer, ecommerce, shopify, amazon ads, retail, omnichannel,
                supply chain, packaging, natural products, expo west
  LOW (5pts):   marketing, brand, startup, fundraising, acquisition, growth

Health & Wellness:
  HIGH (25pts): supplement, nutraceutical, wellness brand, gummy, probiotic, functional food,
                meta health ads, health data restrictions, medical device dtc, clinical claims
  MED (10pts):  dtc health, telehealth, wellness, clean label, gmp, fda, ftc, amazon supplements
  LOW (5pts):   health, fitness, nutrition, self-care

Digital Marketing / Agency:
  HIGH (25pts): ppc, paid media, roas, cpa, meta ads, google ads, performance marketing,
                ad creative testing, media buying, marketing agency
  MED (10pts):  seo, content marketing, email marketing, klaviyo, conversion rate, landing page,
                retargeting, attribution, ga4, gtm
  LOW (5pts):   ai marketing, automation, saas, analytics

Beauty & Personal Care:
  HIGH (25pts): beauty brand, skincare, cosmetics, clean beauty, press-on nails, dermatologist,
                sephora, ulta, beauty dtc
  MED (10pts):  influencer, ugc, tiktok shop, social commerce, beauty trends
  LOW (5pts):   self-care, personal care, grooming
```

## Workflow

```
Task Progress:
- [ ] Step 1: Scan all sources
- [ ] Step 2: Score and rank trends
- [ ] Step 3: Validate top trends (optional Ahrefs)
- [ ] Step 4: Generate content angles
- [ ] Step 5: Output report
```

### Step 1: Scan Sources

Run all scans in parallel using agents or sequential web fetches.

#### 1A. Google Trends (US)

```bash
# Fetch Google Trends RSS (no API key needed)
curl -s "https://trends.google.com/trending/rss?geo=US"
```

Parse the RSS feed. Extract title + approximate traffic for each trending topic.

#### 1B. Reddit

Scan hot posts from these subreddits (use WebFetch or WebSearch):

```
Marketing subreddits: r/marketing, r/PPC, r/SEO, r/digital_marketing, r/ecommerce
Industry subreddits: r/CPG (if exists), r/smallbusiness, r/entrepreneur, r/startups, r/DTC
Niche subreddits: r/SkincareAddiction, r/Supplements, r/FoodIndustry
```

For each subreddit, fetch the top 10 hot posts. Extract: title, score (upvotes), comment count, URL.

#### 1C. Hacker News

```
WebFetch: https://hacker-news.firebaseio.com/v0/topstories.json
```

Get the top 30 story IDs, then fetch each story's details. Filter to stories matching niche keywords.

#### 1D. X/Twitter (optional, requires Brave API)

If `BRAVE_API_KEY` is set, use Brave Search to find trending X/Twitter discussions:

```
WebSearch: "site:x.com OR site:twitter.com [niche keyword] [this week]"
```

Run one search per niche.

#### 1E. YouTube Outlier Detection (optional)

Search YouTube for recent videos (past 7 days) in target niches with unusually high view counts. Use WebSearch:

```
WebSearch: "site:youtube.com [niche keyword] [this month]"
```

Flag videos with view counts significantly above the channel's average.

### Step 2: Score and Rank

For each trend/topic found:

1. **Extract the core topic** (strip platform noise, normalize to a keyword phrase)
2. **Score relevance** against the niche keyword lists:
   - Match against HIGH keywords: +25 points each
   - Match against MED keywords: +10 points each
   - Match against LOW keywords: +5 points each
   - Cap total score at 100
3. **Add engagement bonus:**
   - Reddit: score > 500 upvotes = +10, > 100 comments = +5
   - HN: score > 200 points = +10
   - Google Trends: "Breakout" traffic = +15, > 100K searches = +10
4. **Threshold:** Only surface trends scoring >= 20

Sort by score descending. Deduplicate (same topic from multiple sources = merge, take highest score + note all sources).

### Step 3: Validate Top Trends (Optional)

If Ahrefs token is available, validate the top 10 trends:

```python
# Check if the trend has search volume
GET https://api.ahrefs.com/v3/keywords-explorer/overview
Headers: Authorization: Bearer {AHREFS_TOKEN}
Params: keywords={trend_keyword}, country=us
```

Pull: search volume, keyword difficulty, CPC, traffic potential.

This separates flash-in-the-pan trends (high social buzz, zero search volume) from durable opportunities (social buzz + search demand).

### Step 4: Generate Content Angles

For each trend scoring >= 20, suggest:

1. **Content angle** -- How Jetfuel or a client could write about this
2. **Content type** -- LinkedIn post, blog post, or both
3. **Urgency** -- "Publish today" (breaking), "This week" (trending), "This month" (emerging)
4. **Target audience** -- Which prospect cluster or client vertical this serves
5. **Hook** -- A one-line opening for a LinkedIn post

**Angle frameworks:**
- **Hot take:** Contrarian opinion on the trend ("Everyone's excited about X. Here's why it won't work for most brands.")
- **How-to:** Practical application ("How to use X for your CPG brand's retail launch")
- **Data drop:** Cite the trend data + add your own insight ("Reddit is blowing up about X. Here's what the actual data says.")
- **Case study hook:** Connect to client work ("We just dealt with exactly this for a wellness brand...")

### Step 5: Output Report

Format as a markdown report:

```
## Trend Scout Report — {date}

### Top Trends by Relevance

| # | Topic | Score | Sources | Volume (if available) | KD | Urgency |
|---|-------|-------|---------|----------------------|----|---------|
| 1 | {topic} | {score} | Reddit, HN | {vol} | {kd} | This week |

### Content Angles

**1. {Topic}** (Score: {n})
- Sources: {where it was found}
- Angle: {content angle}
- Type: {LinkedIn post / blog / both}
- Urgency: {publish today / this week / this month}
- Hook: "{one-line opening}"
- Target: {prospect cluster or client vertical}

### Trends by Niche
- CPG / Food & Bev: {count} trends
- Health & Wellness: {count} trends
- Digital Marketing: {count} trends
- Beauty: {count} trends

### Low-Relevance Trends (for awareness)
{List trends scoring 10-19 that didn't hit threshold but are worth monitoring}
```

Also save JSON output to `output/trend-scout-{date}.json` for programmatic use.

## Recommended Cadence

- **2x/week** (Tuesday + Thursday mornings): Full scan
- Pair with `/start-of-day` for trend-aware morning briefings
- Feed top trends into `/abm-content` for prospect-targeted posts
- Feed validated trends into `/write-content` for blog posts

## Integration with Other Skills

| Skill | How Trend Scout Feeds It |
|-------|-------------------------|
| `/abm-content` | Trending topics become LinkedIn posts targeting prospect clusters |
| `/write-content` | Validated trends (volume + KD) become blog post topics |
| `/social-content` | Hot takes and data drops for Edwin's LinkedIn |
| `/content-gaps` | Emerging topics that have no existing content = gaps to fill |
| `/cold-email` | Reference trending topics in outreach: "You've probably seen X trending..." |
