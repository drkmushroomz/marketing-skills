---
name: gsc-report
description: Google Search Console performance report — top queries, top pages, period-over-period changes, and opportunities
disable-model-invocation: true
---

# GSC Report

Pull a Google Search Console performance report for a site. Shows top queries, top pages, period-over-period trends, and identifies opportunities (rising queries, declining pages, high-impression/low-CTR gaps).

## Arguments

The user may specify:
- A site alias (e.g., "train-with-dave"). Default: use the only site in config, or ask if multiple.
- `--lookback N` days for the current period. Default: 30.
- `--compare` to include period-over-period comparison. Default: yes.
- `--query "term"` to filter to queries containing a specific term.
- `--page "url"` to filter to a specific page or URL pattern.

## Steps

1. **Load identity and config:**
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
   - Read `mcp-servers/google-search-console/config.json` for site mappings.

2. **Get today's date** via shell command (`date`). GSC data has ~3 day lag, so the effective end date is today minus 3 days.

3. **Pull data using the GSC MCP tools.** IMPORTANT: Always use `limit: 25` to prevent context overflow. Never use the default limit of 50-100.

   Run these in parallel where possible:

   a. **Top queries** — `gsc_top_queries` with limit 25
   b. **Top pages** — `gsc_top_pages` with limit 25
   c. **Period comparison (queries)** — `gsc_compare_periods` with dimension "query", limit 25
   d. **Period comparison (pages)** — `gsc_compare_periods` with dimension "page", limit 25

   If the user specified a query or page filter, pass it through to the relevant tools.

4. **Present the report:**

   ### Google Search Console: {site_label}
   **Period:** {date_start} to {date_end} vs. prior {N} days

   ---

   ### Top Queries by Clicks
   | Query | Clicks | Impressions | CTR | Avg Position |
   |-------|--------|-------------|-----|-------------|
   | {query} | {n} | {n} | {pct}% | {n} |

   Show top 15. Format CTR as percentage (multiply by 100). Round position to 1 decimal.

   ---

   ### Top Pages by Clicks
   | Page | Clicks | Impressions | CTR | Avg Position |
   |------|--------|-------------|-----|-------------|
   | {short_path} | {n} | {n} | {pct}% | {n} |

   Show top 15. Truncate full URLs to just the path (remove domain). Format CTR as percentage.

   ---

   ### Biggest Movers (Queries)

   **Rising** (clicks increased):
   | Query | Clicks | Change | Position | Pos Change |
   |-------|--------|--------|----------|-----------|
   | {query} | {n} | +{n} | {n} | +{n} |

   Show top 10 risers sorted by clicks_change descending. Positive position_change = improved (moved up).

   **Declining** (clicks decreased):
   | Query | Clicks | Change | Position | Pos Change |
   |-------|--------|--------|----------|-----------|
   | {query} | {n} | {n} | {n} | {n} |

   Show top 10 decliners sorted by clicks_change ascending.

   ---

   ### Opportunities

   **High impressions, low CTR** — queries where the site is showing up but not getting clicked:
   - Filter to queries with impressions > median AND CTR below 3%
   - These are candidates for title tag / meta description optimization
   - Show as table: Query | Impressions | CTR | Position

   **Almost page 1** — queries ranking position 8-20 (bottom of page 1 or top of page 2):
   - These are the easiest wins — a small ranking improvement could significantly increase clicks
   - Show as table: Query | Impressions | Position | CTR

   **New queries** — queries that appear in current period but not in previous:
   - These represent emerging traffic — worth monitoring and potentially building content around
   - List them with clicks and position

   ---

   ### Summary

   - Total clicks and impressions for the period
   - Overall CTR
   - Count of rising vs declining queries
   - Top 3 actionable recommendations based on the data

5. **Ask the user:**
   - "Want me to dig into a specific page or query?"
   - "Want me to inspect any URLs for indexing issues?"
   - "Want me to check a longer time range?"

## Important Rules

- **Always use limit: 25** on all GSC tool calls. Large result sets crash the session.
- Format CTR as a percentage (e.g., 0.0523 → 5.2%), not as a decimal.
- Shorten page URLs to paths only — `/blog/my-post` not `https://trainwithdaveoc.com/blog/my-post`.
- Position is inverted: lower number = better ranking. When showing "position change," positive = improved (moved up in rankings).
- GSC data has a 3-day lag. Always note this in the report header.
- If a site alias isn't found in config, list available aliases and ask the user to pick.
- Round all numbers: clicks/impressions as integers, CTR to 1 decimal, position to 1 decimal.
