---
name: content-gaps
description: Analyze gaps across LLM/AIO visibility, organic rankings, and existing blog content — propose upgrades to titles, descriptions, and content in a Google Sheet
disable-model-invocation: true
---

# Content Gap Analyzer

Cross-reference LLM/AIO visibility, Google Search Console organic data, and existing jetfuel.agency blog content to find gaps and propose specific upgrades. Output everything to a Google Sheet the team can act on.

## Arguments

The user may specify:
- `--focus "topic"` to narrow the analysis to a specific topic cluster (e.g., "meta ads", "cpg"). Default: all clusters.
- `--lookback N` days for GSC data. Default: 90.
- `--refresh` to update an existing sheet instead of creating a new one.

## Setup

1. Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
2. Read `.claude/me.json` for WordPress credentials and user preferences.
3. Read config from `.claude/ops/content-gaps/config.json`.
4. Get today's date via shell command (`date`). GSC data has a ~3-day lag.

## Phase 1: Crawl Existing Blog Content

The blog inventory is the foundation. You need to know what exists before you can find gaps.

### 1A. Pull all published blog posts from WordPress REST API

Use curl to fetch all published posts from the WordPress API:

```bash
curl -s "https://jetfuel.agency/wp-json/wp/v2/posts?per_page=100&page=1&status=publish&_fields=id,title,slug,excerpt,date,modified,link,categories,tags" \
  -u "edwin:{app_password from me.json}"
```

Paginate until you have all posts (check response headers for `X-WP-TotalPages`).

For each post, capture:
- **ID, title, slug, URL**
- **Publish date and last modified date**
- **Excerpt** (this is the meta description in most cases)
- **Categories and tags**

### 1B. Fetch and analyze each blog post's content

For the top 50 posts by recency (or all if fewer than 50), use WebFetch to analyze each post:

```
WebFetch URL: {post.link}
Prompt: "Extract: 1) The H1 title, 2) All H2 headings, 3) Approximate word count,
4) Whether it has FAQ schema, 5) Whether it has a comparison table,
6) The meta description from the <meta name='description'> tag,
7) The first 2 sentences of the article (the AIO extraction target),
8) Any data/stats cited with sources"
```

Build a content inventory with these fields per post:
| Field | Source |
|-------|--------|
| URL | WordPress API |
| Title (H1) | WebFetch |
| Publish date | WordPress API |
| Last modified | WordPress API |
| Word count (approx) | WebFetch |
| H2 headings | WebFetch |
| Has FAQ schema | WebFetch |
| Has comparison table | WebFetch |
| Meta description | WebFetch |
| Opening paragraph | WebFetch |
| Primary topic cluster | Inferred from title + H2s |

Rate-limit WebFetch calls: batch 5 at a time with brief pauses to avoid hammering the site.

## Phase 2: Pull Organic Search Data

### 2A. Google Search Console — Query Performance

Run a Python script using the GSC API (same pattern as `scripts/gsc_pull.py`) to pull data for `sc-domain:jetfuel.agency`:

**Query-level data (last 90 days):**
```python
dimensions: ["query"]
rowLimit: 5000
```

**Page-level data:**
```python
dimensions: ["page"]
rowLimit: 500
```

**Query x Page (for matching queries to landing pages):**
```python
dimensions: ["query", "page"]
rowLimit: 5000
```

Use the OAuth tokens from `config.oauth.tokens_file`. If expired, tell the user to run `python3 scripts/gsc_auth.py`.

From this data, compute:
- **Per-page metrics:** total clicks, impressions, avg position, avg CTR
- **Per-query metrics:** clicks, impressions, position, CTR, landing page
- **Striking distance queries:** position 5-20, impressions >= 20
- **Low-CTR pages:** pages with impressions > 100 but CTR below expected for their position
- **Zero-click pages:** pages with impressions but 0 clicks in 90 days

### 2B. Google Analytics 4 — Organic Landing Page Performance (if available)

Try to pull GA4 data using the Google Analytics Data API. Use the same OAuth credentials with the `analyticsdata` scope.

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric

# Dimensions: landingPage, sessionDefaultChannelGroup
# Metrics: sessions, engagedSessions, engagementRate, averageSessionDuration,
#          bounceRate, conversions, eventCount
# Filter: sessionDefaultChannelGroup == "Organic Search"
# Date range: last 90 days
```

If GA4 API access isn't available (missing scope or property ID), note this in the output and proceed with GSC data only. Add a row in the Summary tab: "GA4 data: not available — run /connect to set up."

From GA4, compute per landing page:
- Organic sessions
- Engagement rate
- Avg session duration
- Bounce rate
- Conversions (if goals are configured)

### 2C. Merge GSC + GA4 + Content Inventory

Join all three datasets on URL/page path. Every blog post should now have:
- Content attributes (title, word count, age, structure)
- GSC metrics (clicks, impressions, position, CTR)
- GA4 metrics (sessions, engagement, bounce rate) — if available

Flag posts that have no GSC data at all (zero impressions in 90 days = likely deindexed or no organic visibility).

## Phase 3: LLM/AIO Visibility Analysis

This phase identifies where jetfuel.agency content should appear in LLM-generated answers but doesn't.

### 3A. Identify high-value LLM prompts per topic cluster

For each topic cluster in the config (or the focused cluster), generate 3-5 prompts using the methodology from `.claude/skills/llm-prompt-research/SKILL.md`:

- **Problem/Symptom:** "My [situation], what should I [do]?"
- **Buyer-Intent Shopping:** "I'm looking for [service] for [niche]. What agencies are good?"
- **Comparison/Validation:** "Is [Jetfuel approach] better than [common approach]?"
- **How-to:** "How do I [task] for [niche]?"

Focus on prompts where an existing blog post SHOULD be the answer but may not be.

### 3B. Test LLM retrieval for each prompt

For each prompt, use `mcp__google-workspace__search_custom` (Google Programmable Search) to check:
1. Does any jetfuel.agency page appear in the top 10 results?
2. Which competitor URLs dominate?
3. What content type ranks (blog post, service page, guide, tool)?

Also use WebSearch to check what a general search returns for these prompts.

### 3C. Score LLM readiness of existing content

For each blog post that SHOULD answer an LLM prompt, score its AIO readiness:

| Factor | Points | Criteria |
|--------|--------|----------|
| Direct answer in opening paragraph | 0-3 | Self-contained, quotable, definitional |
| H2 sections independently extractable | 0-2 | Each section makes sense out of context |
| FAQ with H3 question headings | 0-2 | Natural-language questions, concise answers |
| Comparison tables | 0-1 | HTML tables for any X-vs-Y content |
| Structured data (Article + FAQPage) | 0-1 | Schema markup present |
| Third-party stats cited with links | 0-1 | Verifiable external data points |

**AIO Score: 0-10.** Posts scoring below 5 need AIO upgrades.

### 3D. Cross-reference with existing SEO Opportunities sheet

If the SEO Opportunities sheet exists (check `config.seo_opportunities_sheet_id`), read the **LLM Visibility** and **SEO + LLM Overlap** tabs using `mcp__google-workspace__read_sheet_values`. Pull any previously identified LLM prompts and gaps to avoid duplicating work.

## Phase 4: Gap Analysis & Recommendations

Now synthesize all three data layers into actionable recommendations.

### 4A. Title & Meta Description Upgrades

Find pages where the title or meta description is hurting performance:

**Trigger conditions:**
- CTR below expected for position (< 5% at position 1-3, < 3% at position 4-5, < 2% at position 6-10)
- Meta description is missing, truncated (>160 chars), or generic
- Title doesn't include the primary query driving impressions to that page
- Title is too long (>60 chars) and gets truncated in SERPs

**For each flagged page, propose:**
- A new title tag (under 60 chars, includes primary keyword, compelling)
- A new meta description (under 155 chars, includes keyword, written as a value proposition)
- Reasoning: which GSC query drove this recommendation

### 4B. Content Refresh Opportunities

Find existing posts that should be updated rather than replaced. This phase uses the
[Orbit Media 22-Point Web Content Checklist](https://www.orbitmedia.com/blog/web-content-checklist-17-ways-to-publish-better-content/)
and Andy Crestodina's [content update methodology](https://www.orbitmedia.com/blog/update-old-blog-posts/)
to score each post and prescribe specific upgrades.

#### Prioritization: which posts to update

Rank candidates using three signals (Crestodina's framework):

1. **Near-winners (pos 5-20):** Already recognized by Google; a refresh can push them to page 1.
   Use GSC → filter average position > 5 and < 20, sort by impressions descending.
2. **Declining performers:** Pages that lost >20% organic clicks quarter-over-quarter.
3. **Outdated evergreen content:** Published >12 months ago, still getting impressions, but
   contains stale data/years/examples.

Additional trigger conditions:
- Word count under 1,000 on a topic where competitors have 2,000+ word guides
- Missing FAQ section, comparison tables, or structured data
- AIO score below 5 (needs LLM optimization)
- GA4 engagement rate below 40% (content isn't holding attention)

#### Decide: Light touch vs. full rewrite

- **Light touch** — Title/meta update, fix broken links, swap outdated stats. Use when
  the post already ranks well (pos 1-5) but CTR is low or data is stale.
- **Medium refresh** — Add 500-1,000+ words, new H2 sections, FAQ, comparison tables,
  internal links, updated examples. Use for striking-distance posts (pos 5-15).
- **Full rewrite (URL recycle)** — Treat the URL as a blank page and write a completely
  new article at the same address. Preserves existing backlinks and authority.
  Use when word count is critically low (<1,000) or AIO score ≤ 2.

#### 22-Point Content Checklist audit

For each post flagged for refresh, score it against this checklist (derived from
[Orbit Media's 22-Point Checklist](https://www.orbitmedia.com/wp-content/uploads/2020/10/Orbit-Media-Studios-Web-Content-Checklist.pdf)).
Mark each item Pass / Fail / N/A:

**SEO (5 items):**
1. **Title tag** — includes target keyphrase near the beginning, under 55 chars
2. **H1 header** — includes topic + keyphrase
3. **Primary keyphrase density** — appears 2-3× per 1,000 words in body
4. **Semantic coverage** — includes related phrases, subtopics, People Also Ask answers
5. **Meta description** — sentence summary with keyphrase, under 155 chars

**Human Psychology (11 items):**
6. **Secondary headline** — H1 includes a number or clear benefit after a colon/dash
7. **Subheads (H2s)** — every section has a clear, descriptive H2
8. **Lists** — bulleted or numbered lists make content scannable
9. **Short paragraphs** — no paragraph longer than 4 lines
10. **Formatting** — bold, italics, and block quotes highlight key takeaways
11. **Internal links** — links to at least one other blog post AND one service page;
    bonus: add a link FROM an older high-authority post TO this one
12. **Contributor quotes** — quotes from outside experts with attribution
13. **Examples and evidence** — claims supported by specific data with cited sources
14. **Length / detail** — related questions answered, examples provided, complete yet concise
15. **Call to action** — invitation to subscribe, download, or contact
16. **Author box** — author photo, bio, links to social profiles

**Additional Media (6 items):**
17. **Featured image** — compelling, shareable image for social snippets
18. **Supportive visuals** — images/charts at every scroll depth so one is always visible
19. **Video** — embedded video near top with custom thumbnail (face + headline)
20. **Audio** — embedded podcast or audio player (if applicable)
21. **Social sharing** — tweetable/shareable quotes or stats
22. **Downloadable asset** — PDF, template, or gated resource (if applicable)

**Checklist score:** Count of Pass items out of applicable items (exclude N/A).
Posts scoring below 12/22 need Medium or Heavy refresh.

#### For each flagged post, prescribe:
- **Checklist score** and which items failed
- Specific sections to add (based on what competitors cover that we don't)
- H2 headings to add
- FAQ questions to add (from People Also Ask + LLM prompt gaps)
- Whether to add comparison tables or data visualizations
- Internal linking plan: which existing high-authority posts should link TO this one
- Broken links to fix, outdated stats/years to replace
- Media gaps: missing visuals, video, downloadable asset
- Estimated effort: Light / Medium / Heavy (full rewrite)
- **URL recycle candidate?** Yes/No — if yes, note the existing backlink count from GSC

#### After the refresh: re-promotion plan
- Update the publish date (republish to top of blog)
- Re-share on social channels with "updated for [year]" framing
- Email the post to list segments relevant to the topic
- Notify any contributors quoted in the updated version

### 4C. New Content Gaps

Find topics where no jetfuel.agency content exists but should:

**Sources of gap signals:**
- GSC queries with impressions but no dedicated page
- LLM prompts where jetfuel.agency doesn't appear and no blog post covers the topic
- Topic cluster x service combinations with no content (e.g., "tiktok ads for food brands")
- Competitor content that ranks well with no Jetfuel equivalent
- Queries from the SEO Opportunities sheet marked "Create new content"

**For each gap, propose:**
- Recommended title (H1)
- Target keyword cluster
- Recommended content type (blog post, guide, service page)
- Which LLM prompts it would answer
- Priority: High (commercial intent + volume), Medium (informational + volume), Low (long-tail)

### 4D. LLM Visibility Gaps

Separate tab for AIO-specific opportunities:

**For each gap:**
- The LLM prompt (conversational, not keyword-style)
- Whether an existing post could answer it (with URL) or if new content is needed
- Current status: "Not appearing", "Appearing but not cited", "Competitor dominates"
- Which competitor currently gets cited
- Specific AIO upgrades needed (opening paragraph rewrite, FAQ addition, table addition, schema markup)

## Phase 5: Write to Google Sheet

Create a new Google Sheet (or update existing if `--refresh`) using `mcp__google-workspace__create_spreadsheet` and `mcp__google-workspace__modify_sheet_values`.

### Tab 1: "Content Audit"
Full inventory of all existing blog posts with merged metrics.

| URL | Title | Publish Date | Last Modified | Word Count | Has FAQ | Has Tables | AIO Score | GSC Clicks (90d) | GSC Impressions | Avg Position | CTR | GA4 Sessions | Engagement Rate | Primary Cluster |

Sort by GSC impressions descending. Apply conditional formatting:
- AIO Score < 5: red background
- CTR below expected: orange background
- Last Modified > 12 months ago: yellow background

### Tab 2: "Title & Meta Upgrades"
Pages where title or description changes would improve CTR.

| URL | Current Title | Proposed Title | Current Meta | Proposed Meta | Primary Query | Position | Impressions | Current CTR | Expected CTR Lift | Priority |

Sort by expected impact (impressions x CTR gap) descending.

### Tab 3: "Content Refresh"
Existing posts that need updating, scored against the 22-point checklist.

| URL | Title | Publish Date | Why Refresh | Checklist Score | Failed Items | Sections to Add | FAQ Questions to Add | Add Tables? | Internal Links to Add | Media Gaps | Effort | URL Recycle? | Impressions | AIO Score | Priority |

Sort by priority (High > Medium > Low), then by impressions.
Effort = Light (title/meta only), Medium (add 500+ words + FAQ + tables), Heavy (full rewrite at same URL).

### Tab 4: "New Content Gaps"
Topics where no content exists.

| Recommended Title | Target Keyword Cluster | Content Type | LLM Prompts It Answers | Search Intent | Competitor URLs Ranking | Estimated Monthly Impressions | Priority |

Sort by priority, then estimated impressions.

### Tab 5: "LLM Visibility Gaps"
AIO-specific opportunities.

| LLM Prompt | Prompt Type | Existing Post URL | Status | Competitor Cited | AIO Upgrades Needed | New Content Required? | Priority |

Prompt Type = Problem/Symptom, Buyer-Intent, Comparison, How-to

### Tab 6: "Summary"
Executive overview.

| Metric | Value |
|--------|-------|
| Total blog posts audited | {n} |
| Posts with zero organic clicks (90d) | {n} |
| Posts needing title/meta upgrades | {n} |
| Posts needing content refresh | {n} |
| New content gaps identified | {n} |
| LLM visibility gaps | {n} |
| Average AIO readiness score | {n}/10 |
| Top 5 priority actions | {list} |
| GSC data range | {dates} |
| GA4 data available | Yes/No |

## Output

After writing to the sheet, print a summary to the conversation:

```
## Content Gap Analysis — jetfuel.agency
Generated: {date}

### Blog Inventory: {n} posts audited
- {n} getting organic traffic | {n} with zero clicks in 90 days
- Average AIO readiness: {n}/10

### Title & Meta Upgrades: {n} pages
[Top 3 highest-impact title changes with current vs proposed]

### Content Refresh: {n} posts
[Top 3 highest-priority refreshes with what needs to change]

### New Content Gaps: {n} topics
[Top 3 missing topics with recommended titles]

### LLM Visibility Gaps: {n} prompts
[Top 3 prompts where Jetfuel should appear but doesn't]

### Recommended Priority Actions
1. ...
2. ...
3. ...
4. ...
5. ...

Full report: [Google Sheet link]
```

## Important Rules

- **Always use `marketing@jetfuel.agency`** for Google API calls (GSC, GA4, Sheets, Drive).
- **GSC API: use `limit: 25` on MCP tool calls** to prevent context overflow. For Python scripts, you can use higher limits (1000-5000) since they run outside context.
- **Rate-limit WebFetch:** no more than 5 concurrent fetches. The site is on shared hosting.
- **Never fabricate metrics.** If GA4 isn't available, leave those columns blank. If GSC data is sparse, note it. A gap analysis with real data for 30 posts is better than fake data for 100.
- **Proposed titles must be under 60 chars.** Proposed meta descriptions under 155 chars. These are hard SERP limits.
- **LLM prompts must be conversational** — how a real person would ask ChatGPT, not a Google keyword. Follow the methodology in `.claude/skills/llm-prompt-research/SKILL.md`.
- **Don't recommend creating content that already exists.** Always check the content inventory first. If a post covers the topic but poorly, it's a refresh, not a gap.
- **Prioritize commercial intent.** A query like "food and beverage marketing agency" matters more than "what is digital marketing" — weight accordingly.
- **Cross-reference with existing SEO Opportunities sheet** to avoid duplicating prior analysis. Build on it, don't repeat it.
- **Display all times in the user's timezone** (from me.md).
- **The Google Sheet is the deliverable.** The in-conversation summary is just a preview. Put all the detail in the sheet.
