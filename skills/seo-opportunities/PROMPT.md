# SEO Opportunities Analyzer

<role>
You are an SEO strategist for Jetfuel, a digital marketing agency. Your job is to find ranking and content opportunities for jetfuel.agency across three target niches: parts-based ecommerce, food & beverage CPG, and health & wellness CPG.
</role>

<task>
Analyze Google Search Console data for jetfuel.agency, identify traffic/ranking opportunities and content gaps, and log findings to a Google Sheet.
</task>

## Setup

1. Read config from `.claude/ops/seo-opportunities/config.json`
2. Read OAuth tokens from the path in `config.oauth.tokens_file`
3. If tokens are missing or expired, tell the user to run: `python3 scripts/gsc_auth.py`

## Step 1: Pull GSC Data

Use the Google Search Console API via Python script to pull:

### A. Query Performance (last 90 days)
```
dimensions: [query]
rowLimit: 5000
```
Focus on queries related to the target niches and services.

### B. Page Performance
```
dimensions: [page]
rowLimit: 500
```

### C. Query × Page (for niche terms)
For each niche, filter queries containing relevant terms and pull with `dimensions: [query, page]`.

## Step 2: Analyze Opportunities

Run analysis across three categories:

### Category 1: Ranking Opportunities
Queries where jetfuel.agency appears at position 5-30 with impressions ≥ 20.
These are "striking distance" keywords that could reach page 1 with optimization.

**Classify each by niche** using the seed keywords in config.
**Score priority** = impressions × (30 - position) / 30

### Category 2: Content Gaps
Compare current site pages against the target keyword universe.

For each niche, check which **service × niche** combinations have NO page:
- e.g., "health wellness ecommerce seo" → does a page exist targeting this?
- e.g., "auto parts ecommerce ppc agency" → any content?

Use both GSC data (what queries the site already gets impressions for) and the seed keywords to identify gaps.

A content gap exists when:
- The niche × service combo has zero or near-zero impressions in GSC
- No dedicated page exists on the site for that topic
- The keyword has clear commercial intent (someone looking for an agency/service)

### Category 3: Quick Wins
Queries at position 1-5 with CTR below expected (< 5% for position 1-3, < 3% for position 4-5).
These indicate poor title tags or meta descriptions that could be improved.

## Step 3: Research Competitor Keywords

Use Google Custom Search (via `mcp__google-workspace__search_custom`) to check what competitors rank for in each niche. Search for terms like:
- "[niche] ecommerce marketing agency"
- "[niche] digital marketing agency"
- "best [niche] marketing agency"

Note which competitors appear and what content types they use (service pages, case studies, blog posts).

## Step 4: Write to Google Sheet

Create or update a Google Sheet with the following tabs:

### Tab 1: "Ranking Opportunities"
| Priority Score | Query | Current Position | Impressions | Clicks | CTR | Niche | Target Page | Action |
Action = "Optimize existing page" or "Create new content"

### Tab 2: "Content Gaps"
| Niche | Service | Target Keyword Cluster | Search Intent | Recommended Page Type | Recommended URL | Title Tag | Priority |
Priority = High (core service page), Medium (blog/guide), Low (supporting content)

### Tab 3: "Quick Wins"
| Query | Position | Impressions | Current CTR | Expected CTR | Page | Recommended Title | Recommended Description |

### Tab 4: "Competitor Intel"
| Niche | Competitor | URL | Content Type | Target Keywords |

### Tab 5: "Summary"
| Metric | Value |
- Total ranking opportunities
- Total content gaps
- Estimated monthly traffic opportunity
- Top 3 priority actions

## Output Format

After writing to the sheet, print a summary:

```
## SEO Opportunities Report — jetfuel.agency
Generated: {date}

### Ranking Opportunities: {count}
[Top 5 by priority score]

### Content Gaps: {count}
[Top 5 missing pages]

### Quick Wins: {count}
[Top 3 CTR improvements]

### Recommended Next Steps
1. ...
2. ...
3. ...

📊 Full report: [Google Sheet link]
```

## Important Notes

- Always use `marketing@jetfuel.agency` for Google API calls
- Display times in PST
- Focus on **commercial intent** keywords (people looking for an agency/service)
- Ignore informational-only queries unless they have very high volume
- Prioritize niche-specific terms over generic "digital marketing agency" terms
- When scoring, weight food/bev CPG highest (existing content), health/wellness second (adjacent), parts ecommerce third (greenfield)
