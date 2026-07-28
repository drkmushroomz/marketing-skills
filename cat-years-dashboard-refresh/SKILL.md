---
name: cat-years-dashboard-refresh
description: Daily cron refresh of the Cat Years tracking dashboard. Pulls Klaviyo + jetfuel-hq + Meta ads data and overwrites the live tabs in the Google Sheet.
---

# Cat Years Dashboard Refresh

Idempotent daily refresh of the Cat Years tracking dashboard. Runs at 7am PT via Windows Task Scheduler. Pulls fresh data from Klaviyo and jetfuel-hq, computes aggregates, overwrites the relevant tabs in the sheet.

**Spreadsheet:** `1WK_vRN2-YpeDgpMeP7C9XKi2wWXja2wPxD-FmIflcME`
**Owner email for MCP calls:** `edwin@jetfuel.agency`
**Klaviyo account:** Cat Years (org id `SChnvL`, sender catyears.com)
**Cat Years HQ client id:** `64`

## What to overwrite

These tabs get rewritten every run. Other tabs (Targets, Pre-Launch Audit, UTM Reference, Funnel by Source headers, Sample-to-Buyer Cohort) are static or manually maintained, leave them alone.

- `Exec Summary!A1:C42`
- `Daily Channel Performance!A2:AA50` (clear then write)
- `CPS Pacing!A2:M50` (clear then write)
- `Funnel by Source!A2:N9` (just refresh totals row)
- `Creative Performance!A2:Q30` (clear then write)
- `Leads Log!A2:AD51` (clear then write - 50 newest profiles)
- `Viral Health!A2:K5` (refresh if Gleam launches; otherwise re-write the "not launched" note)
- `Flow Performance (A/B)!A2:R30` (clear then write per-message stats + campaign stats)

## Step 1 - Date range

Window = last 30 days. Use Bash `date -v -30d +%Y-%m-%d` (macOS) or `date -d '30 days ago' +%Y-%m-%d` (Linux). On Windows use PowerShell `(Get-Date).AddDays(-30).ToString('yyyy-MM-dd')`. Today's date via `Get-Date -Format 'yyyy-MM-dd'`.

The window start is PINNED to `2026-05-25` for the life of this launch report (Edwin 2026-07-03; the hero says "May 25 – <end>" and the launch-scoped sections say "launch to date", so a rolling start would make those labels lie). Do NOT switch to a rolling 30-day start.

## Step 2 - Pull Klaviyo aggregates

Call `mcp__klaviyo__query_metric_aggregates` once per metric with `interval: day`, `timezone: America/New_York`, model `claude`. Use these metric IDs (verified 2026-06-09):

| Metric name | metric_id | measurements |
|---|---|---|
| Quiz Started | `WS89Lm` | count, unique |
| Quiz Completed (the Lead event) | `UxTJ2Z` | count, unique |
| Mail piece sent (Strata outbound) | `T7vkvz` | count, unique |
| Mail piece delivered (Strata) | `WGm7wx` | count, unique |
| Placed Order (Shopify revenue) | `UzD6xZ` | count, unique, sum_value |
| Checkout Started (Shopify) | `VK3VrR` | count, unique |
| Viewed Product (Shopify) | `QYet6K` | count, unique |
| Mail piece received (Strata, RELIABLE) | `Ud2PPs` | count |

Keep the per-day arrays for Quiz Completed (`UxTJ2Z`), Mail piece received (`Ud2PPs`), and Placed Order (`UzD6xZ` count + sum_value) - they feed both the sheet tabs and the client dashboard's `daily` trend series (Step 10).

If a metric ID 404s, the metric was renamed/deleted upstream. Re-call `mcp__klaviyo__get_metrics` and remap by name, then update this skill file inline before continuing.

## Step 3 - Pull Klaviyo segment counts

Call `mcp__klaviyo__get_segment` with `includeProfileCount: true` for:

- `YesmwB` - JF | Quiz Completed (all sources)
- `XWtXJu` - JF | Quiz Completed (Paid Media)

If either segment ID 404s, the segment was deleted/renamed. List segments via `mcp__klaviyo__get_segments` and remap by name.

## Step 4 - Pull recent profiles for Leads Log

Call `mcp__klaviyo__get_profiles` with `page_size: 50`, `sort: -created`, `model: claude`, fields `["email", "first_name", "last_name", "created", "location.city", "location.region", "location.zip", "properties"]`.

**Property name mapping (production keys, NOT the spec names):**
- `signup_source` (NOT `Acquisition_Source`)
- `utm_source_first` (NOT `utm_source`)
- `utm_medium_first` (NOT `utm_medium`)
- `utm_campaign_first` (NOT `utm_campaign`)
- `cat_1_name`
- `utm_content_first`, `utm_term_first`, `offer_group`, `referrer_id`, `viral_depth` are NOT instrumented yet - leave blank if absent

If the profiles response exceeds the tool result limit, you'll get a file path. Dispatch the extraction to a general-purpose subagent with the instructions in the original session (slice via python `read()[A:B]` and return a JSON array of 30 profiles with the keys: klaviyo_profile_id, date_created, email, first_name, last_name, cat_name, acquisition_source, utm_source, utm_medium, utm_campaign, city, region, zip).

## Step 4b - Pull Klaviyo flow + campaign performance (for the Flow Performance / A/B tab)

Call `mcp__klaviyo__get_flow_report` with:
- `conversionMetricId: "UzD6xZ"` (Placed Order)
- `statistics: ["recipients", "delivered", "opens_unique", "open_rate", "clicks_unique", "click_rate", "click_to_open_rate", "conversions", "conversion_uniques", "conversion_rate", "unsubscribes", "bounced", "spam_complaints"]`
- `valueStatistics: ["conversion_value", "average_order_value", "revenue_per_recipient"]`
- `groupBy: ["flow_id", "flow_name", "flow_message_id", "flow_message_name", "send_channel", "variation", "variation_name"]`
- `timeframe: {"key": "last_30_days"}`
- `filters: [{"fieldName": "send_channel", "operator": "equals", "value": "email"}]`

Then call `mcp__klaviyo__get_campaign_report` with the same statistics, valueStatistics, and timeframe; groupBy `["campaign_id", "campaign_message_id", "campaign_message_name", "send_channel", "variation", "variation_name"]`.

**Interpretation:**
- If `variation_name` is empty string on every row, **no A/B test is live**. Write `"(no A/B)"` in the Variation column.
- If two or more rows share the same `flow_message_id` but different `variation_name`, those are A/B variants. Compute uplift % = (variant_rate - control_rate) / control_rate. Mark the winner with `WINNER` and the loser with `LOSER` in a Notes column.
- Statistical significance: flag variants below 95% confidence with `(low confidence)`. Use Recipients >= 1,000 per variant as a minimum bar for confidence.

## Step 5 - Pull jetfuel-hq ads data

If `mcp__claude_ai_jetfuel_hq__client_performance` and `mcp__claude_ai_jetfuel_hq__campaigns_performance` aren't visible, first call `mcp__claude_ai_jetfuel_hq__load_ads_tools`.

Then call in parallel:
- `client_performance` with `client: "Cat Years"`, the date range
- `campaigns_performance` with `client: "Cat Years"`, the date range, `sort_by: spend` (this is the FULL-WINDOW roster used for classification in Step 5a)
- `ads_performance` with `client: "Cat Years"`, the date range, `min_spend: 1`, `sort_by: spend`, `limit: 25` (Meta only - Google ad-level not synced)

## Step 5a - Classify campaigns: sample-driving vs awareness

Edwin's rule (locked 2026-06-21): the sample-CPS metric counts **conversion-optimized "driving samples" spend ONLY**. Awareness, TOF traffic, and engagement spend are EXCLUDED. Classify every campaign from the full-window `campaigns_performance` roster:

**IN (sample-driving):**
- **Meta**: `objective == OUTCOME_LEADS`; OR `objective == OUTCOME_SALES` AND name contains `-sample` (mof-sample / bof-sample) AND name does NOT contain `samplerecipients` / `recipients`.
- **Google Ads**: name contains `[ROI]` AND `[PR]` (prospecting) AND NOT `[RT]` AND `Brand` not in the name - i.e. non-brand prospecting search that acquires NEW sample sign-ups (e.g. `[JF] - [ROI] - [S] - [PR] - Non-Brand - Hydration`, id 1076). The bare `[ROI]` tag is NOT enough: Brand-Defense and all retargeting also carry it but are ecommerce (see OUT).
- **TikTok**: name contains `mofsample` or `bofsample` (e.g. `jf-mofsample-*`, `jf-bofsample-*`).

**OUT (exclude):**
- Meta `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_TRAFFIC`.
- Meta `samplerecipients_rt_sales*` (retargets already-sampled users for purchase - a buyer conversion, not a new sample).
- Google `[AW]`.
- **Google Brand-Defense (`[MIX]` + `Brand` in name, id 1075) and ALL Google `[RT]` retargeting (`[RT]` in name, ids 1081/1078/1079) - these are ECOMMERCE / purchase-driving, NOT sample acquisition (Edwin 2026-07-16). They carry the `[ROI]` tag but do not drive new sample sign-ups.**
- TikTok `tof-*` (video views / reach / spark), `delete`, `shell`/`dontrun` shells.
- **Any campaign you cannot confidently classify → EXCLUDE it and log its name** under "Issues detected" so a human can re-check. Never silently include an ambiguous campaign.

**D2C CONVERSION (a THIRD bucket - tracked on its own Conversion tab, NOT counted in sample CPS or awareness).** Direct-to-purchase campaigns: Meta `objective == OUTCOME_SALES` AND name contains `d2c` AND name does NOT contain `sample` / `recipients` / `rt`. These are purchase-optimized "buy now, no sample step" campaigns (Débhora launched the first two 2026-07-21: `jf_d2c_ps_sales_asc_scaling` id 2901, `jf_d2caudiencetest_ps_sales_cbo_sandbox` id 2902). They are EXCLUDED from sample-driving spend (they acquire buyers, not samples) and from awareness. Collect their raw per-campaign rows into `D2C_CAMPAIGNS` for the `conversion` block in Step 10. Re-derive the set every run by the name rule; more D2C campaigns launch as the funnel scales.

Build `SAMPLE_CAMPAIGN_IDS` = the set of IN campaign IDs. Known IN ids as of 2026-07-16: Meta `2875` (LEADS), `2872`/`2873` (mof/bof-sample SALES, currently $0); Google `1076` (Non-Brand prospecting ONLY); TikTok `50`, `47`, `42`. Known ECOMMERCE (NOT sample) despite `[ROI]`: Google `1075` (Brand-Defense), `1081`/`1078`/`1079` (RT). Re-derive the set every run - do NOT hardcode, since new campaigns launch weekly.

## Step 5b - Daily sample-driving spend

For each day `D` in the window, call `campaigns_performance` with `client: "Cat Years"`, `date_start == date_end == D`, `metrics: ["spend"]`. Sum `spend` across only the rows whose `id` is in `SAMPLE_CAMPAIGN_IDS`. That gives `sample_spend[D]`. Batch the day-calls in parallel (the window is ≤30 days). Days before sample campaigns launched (pre-2026-06-08) have ~$0 sample spend - leave their Sample Spend / CPS cells blank.

## Step 6 - Compute aggregates

### From Klaviyo daily arrays

For each day in the window, extract: quiz_starts, quiz_completes, mail_sent, mail_delivered, orders, revenue (Placed Order sum_value), checkouts. Sum across the window for the period totals.

### From jetfuel-hq client_performance

- `totals.spend` → total ad spend
- `by_platform[i].spend` per platform (Meta/Facebook, TikTok, Google Ads) → channel breakdown

### CPS calculations

**Sample CPS is the headline metric** (uses sample-driving spend from Step 5a/5b only):
- Daily sample CPS[D] = `sample_spend[D] / quiz_completes[D]` (blank if leads == 0 or no sample spend that day)
- 7-day rolling sample CPS[D] = `sum(sample_spend[D-6..D]) / sum(quiz_completes[D-6..D])` - only populate once a full trailing-7-day launch window exists (from 2026-06-14 on); blank before that
- Period sample CPS = `sum(sample_spend) / sum(quiz_completes)` over the window
- Variance % = `(cps - 7.00) / 7.00` vs the $7 Month-1 target

For context only (NOT the headline):
- Blended CPS (all spend incl awareness) = `client_performance totals.spend / period quiz_completes`
- Paid-only CPS = blended-period spend / XWtXJu segment profileCount

Watch the **trend**, not just the level: compare the latest 7-day rolling sample CPS to the prior week. Rising rolling CPS = the cheap organic/spike leads are thinning and each new sample costs more. Flag it in the log + Exec Summary if the rolling CPS is climbing.

### Funnel rates

- Quiz Start → Complete = quiz_completes / quiz_starts
- Quiz Complete → Mail sent = mail_sent / quiz_completes
- Checkout → Order = orders / checkouts

### Creative dedupe

`ads_performance` returns one row per (ad x poster_url) - dedupe by ad ID for the Creative Performance tab, keep the row with highest spend per ad.

## Step 7 - Write to the sheet

Use `mcp__google-workspace__modify_sheet_values` with `user_google_email: edwin@jetfuel.agency`. **Always overwrite the entire data range, do not append.** This means clearing rows beyond the new data - if today's window has fewer rows than last run, the residual rows would mislead.

Strategy: write a fixed-size range with empty strings padding to the end. For example, Daily Channel Performance gets exactly 30 daily rows + 5 platform rollup rows = 35 rows. If only 16 days have data, pad with blank rows.

### Range writes

For each tab below, write the values then format the period total row bold + yellow.

**Exec Summary `A1:C42`** - see the template at the bottom of this file. Substitute today's numbers.

**Daily Channel Performance `A2:AA50`** - Daily rows by date (channel="ALL") then blank row then platform rollup rows + grand total. Pad with empty rows to row 50.

**CPS Pacing `A2:J50`** - Daily rows, one per date (channel=ALL). Columns:
`Date | Channel | Sample Spend ($) | Leads (Quiz Complete) | Sample CPS ($) | CPS Target ($) | Variance % | 7-Day Rolling Sample CPS ($) | MTD Sample Spend ($) | MTD Leads`
Use `sample_spend[D]` (Step 5b), daily + rolling sample CPS (Step 6), `$7.00` target, and June-cumulative MTD columns. Pre-launch days (pre-2026-06-08): leave Sample Spend / CPS / rolling blank, still show Leads. Then a blank row + a `TOTAL (05-25 to <today>)` row with period sample spend, total leads, period sample CPS, variance, and the latest 7-day rolling in col H. Pad blanks to row 50.
Header note lives in `L1` (do not overwrite): defines Sample Spend = conversion-optimized campaigns only. Row 1 headers are set; rewrite them only if columns change.
NOTE: spend CAN now be split by day via Step 5b per-day `campaigns_performance` calls - the old "can't split spend by day" limitation is retired.

**Funnel by Source `A9:N9`** - Just the TOTAL row at bottom (channel rows stay as placeholders since we don't have per-channel Klaviyo split).

**Creative Performance `A2:Q30`** - Top ~15 unique ads by spend. Dedupe by ad ID. Columns per the header.

**Leads Log `A2:AD51`** - 30 newest profiles. Pad to row 51 if fewer.

**Viral Health `A2:K5`** - If `gleam_entries > 0` in the period (check by looking for a `Gleam` metric in `klaviyo_get_metrics`), populate real numbers. Otherwise re-write: `[today, 0, 0, 0, "n/a", "n/a", 0, 0, 0, 0, "Gleam contest NOT YET LAUNCHED..."]`

**Flow Performance (A/B) `A2:R30`** - One row per (flow_message, variation). Columns:
Flow | Trigger | Message | Variation | Status | Recipients | Delivered | Open Rate (%) | Click Rate (%) | CTOR (%) | Conversion Rate (%) | Conversions | Revenue | AOV | Rev/Recipient | Unsubs | Spam | Notes

Then a blank row, then a `CAMPAIGNS` divider row (gray background), then one row per (campaign_message, variation) with the same columns. Skip campaigns that are tests sent to the internal "Test List" (audience name contains "Test").

If A/B variations are detected (two rows with same flow_message_id, different variation_name), put `WINNER` / `LOSER` + uplift % in Notes.

## Step 8 - Update memory if schema drifts

If you discover during this run that:
- A new Klaviyo property has been added (e.g. `offer_group` finally instrumented)
- A new metric exists (Gleam events appear)
- Strata mail piece volume jumps (the "bottleneck" gets unblocked)

Update the memory file `feedback_cat_years_dashboard.md` (create if missing) with the change. This keeps the next conversation accurate.

## Step 9 - Log + exit

Log run summary to stdout (the bat file pipes to `scripts/_cat_years_dashboard_refresh.log`):

```
=== Cat Years Dashboard Refresh ===
Date: YYYY-MM-DD HH:MM
Window: 2026-05-25 to YYYY-MM-DD
Leads (quiz completed): N
Samples shipped (Strata): N
Orders / Revenue: N / $X
Total spend: $X (Meta $X / TikTok $X / Google $X)
CPS blended: $X | CPS paid-only: $X
Tabs refreshed: 6
Issues detected: (list any)
```

Exit 0 on success, non-zero on any tool error.

## Step 10 - Regenerate + reshare the client-facing HTML dashboard

After the sheet is written, rebuild the client HTML dashboard from the SAME live data and reshare it to HQ Hosted Page **id 15** (`Cat Years - Launch Performance Report`, public URL `share.jetfuel.agency/p/cat-years-launch-report/...`). Do NOT hand-edit HTML - a deterministic renderer does the formatting.

**Reviews:** pull the Judge.me aggregate from Shopify (the Shopify MCP is connected to the Cat Years store). Query product `gid://shopify/Product/9085522837660`:
`mcp__claude_ai_Shopify__graphql_query` → `{ product(id:"gid://shopify/Product/9085522837660"){ reviewsRating: metafield(namespace:"reviews",key:"rating"){value} reviewsCount: metafield(namespace:"reviews",key:"rating_count"){value} } }`
`reviewsCount.value` = review count; `reviewsRating.value` is JSON `{"value":"4.96"}`. If Shopify is unavailable this run, reuse the last known values (173 / 4.96) and note it in the log.

**Sign-up source split (Acquisition Mix section + paid-only CPS).** Run the deterministic helper via Bash:
`python scripts/cy_signup_sources.py --start 2026-05-25 --end <today>`
It pulls GA4 `generate_lead` by first-touch source/medium and buckets into `{paid, freebie, organic, dark, total}` (classification lives in the script - paid = paid mediums, freebie = aggregator/sample sites, organic = earned social+search+owned email, dark = direct/unattributed). Put the object at `signup_sources` in the metrics JSON. The renderer derives Paid CPS = `sample_spend ÷ paid` (Edwin 2026-06-30 - the blended CPS is misleading because ~60% of sign-ups arrive free) and the blended/free-share numbers. **If the helper errors (GA4 auth/quota), reuse the previous run's `signup_sources` from the existing metrics JSON and note it in the log** - do NOT drop the key (the renderer degrades to "n/a" but the section should stay populated). The GA4 paid bucket cross-checks the Klaviyo `XWtXJu` paid segment within ~0.3%.

**Build the metrics JSON.** Write `scripts/_cat_years_dashboard_metrics.json` with RAW (unformatted) numbers. The renderer computes all percentages, cost-per-sample, bar heights, K-formatting, and totals. Full schema + field meanings are documented at the top of `scripts/cat_years_dashboard_render.py`. Source each field:
- `quiz_started` / `quiz_completed` = period totals. `latest_day_reqs` = the most recent FULL day's quiz-completed count (not today's partial). `window_end` e.g. "June 23, 2026"; `updated` "Jun 23"; `days_post_launch` = days since 2026-06-08.
- `delivered` = period **"Mail piece received"** (`Ud2PPs`) - the RELIABLE fulfillment number (homes reached). Do NOT use "Mail piece sent" (`T7vkvz`) for the client HTML: its webhook undercounts (gap after ~2026-06-15, received > sent), confirmed 2026-06-24. The post-sample CVR flow triggers on `Ud2PPs`. `orders` / `revenue` = Placed Order count / sum_value. `checkouts` = Checkout Started count.
- `flows` table shows CTR (= visits ÷ sent) and CVR (= orders ÷ site visits/clicks, the traffic-based conversion - Edwin 2026-06-24), both renderer-derived. Labels are "Sign-Ups" not "sample requests" (Kim 2026-06-24); the renderer keeps tokens, the template carries the wording. The cohort section has NO bar chart (removed as redundant) and cohort cards show only sign-ups + spend + cost/sign-up. The "Performance vs. Goals" section was REMOVED (Edwin 2026-06-24); the report ends at Budget & Spend.
- `total_spend` + per-platform `meta_/google_/tiktok_` spend/impr/clicks/ctr/cpm (Google sends `google_conv` not cpm) from `client_performance`.
- **Audience Quality section (client call 2026-07-02, Jordan; live since page v35).** The `audience` block: (1) `shares` (premium/genpop/freebie/unknown percents) are STATIC from the validated 2026-07-03 stratified sample - CARRY THEM OVER from the previous run's metrics JSON unchanged until the nightly profile-ledger pipeline lands (do NOT recompute from a partial pull, do NOT drop the block). (2) `signups_total` = this run's `quiz_completed`. (3) `buyers` = EXACT sampled buyers per segment: you already match buyer emails to Klaviyo profiles in the Step-10 join; additionally classify each SAMPLED buyer: freebie if `referrer_first` domain is in `KNOWN_FREEBIE_SOURCES` (scripts/cy_freebie_daily.py) or referrer/utm contains a freebie keyword; else premium if profile ZIP's median income >= $65,929 in `.claude/_cy_zip_income_map.json`; else genpop if ZIP in map; else unknown. Sum n + order revenue per segment. Keep `sampled_buyers`/`sampled_buyer_rev`/cohort buyers consistent with the same join.
- **Awareness section (client call 2026-07-02, Jordan).** `awareness` = RAW per-platform sums over AWARENESS campaigns ONLY, from the full-window `campaigns_performance` roster you already pulled. Classify: Meta `objective == OUTCOME_AWARENESS`; Google name contains `[AW]`; TikTok name contains `tofspark` (or `tof` + `videoviews`). Per platform emit `{spend, impr, views, p75}` where `views` = Meta `video_views` (3s plays) / Google `video_views` (30s or full) / TikTok `video_watched_6s`, and `p75` = Meta `video_p75_watched_actions` / TikTok `video_watched_p75` / Google `round(video_quartile_p75_rate * impressions)` per campaign (the API sends a rate, not a count). Keys: `meta`, `youtube`, `tiktok`. Renderer derives CPM, view-through, and 75%-watch rates.
- **Freebie Traffic Watch (client call 2026-07-02, Sarah; policing mechanism for the CDN block).** Run `python scripts/cy_freebie_daily.py` and set `freebie_daily` = its `days` array (14 full days of GA4 sessions; freebie bucket = the canonical 38-site list from ClickUp task 86baqh6nm, which lives in the script as `KNOWN_FREEBIE_SOURCES`). Also set `freebie_block_status` = `"CDN block live since Jul 7"` (Pat's server-level block shipped 2026-07-07, confirmed by Edwin). If a future block/unblock changes this, update the date here. **Watch duty:** if the latest full day's freebie count is NOT trending toward zero after the block is live, or a NEW freebie referrer shows up in `--detail` output that is not in `KNOWN_FREEBIE_SOURCES`, add it to the script's list, mention it under "Issues detected" in the Step 9 log, and update ClickUp task 86baqh6nm. If the script errors (GA4 auth/quota), reuse the previous run's `freebie_daily` and note it in the log; never drop the key.
- **Budget pace resets monthly (Edwin 2026-07-02).** `month1_budget` stays `7500` (it is the recurring monthly budget). Also set `budget_month` = the current calendar month's name (e.g. "July") and `budget_spend_mtd` = total spend from the 1st of the current month through YESTERDAY (complete days only, so it matches `periods.mtd.spend`): one extra `client_performance` call, take `totals.spend`.
- **Period toggle (Edwin 2026-07-03, page v37; scope expanded 2026-07-23).** The topbar pills switch section 01, Budget & Spend, By Channel, AND (added 2026-07-23, Mel flagged the toggle looked broken on the other tabs) the Awareness, Conversion (D2C), and Creative tabs, between `periods.last` (last closed calendar month, frozen) and `periods.mtd` (current month through yesterday). Everything else (the top hero "launch to date" goal card, Samples & Cohorts, sample-to-buyer attribution) is intentionally cumulative launch-to-date and does NOT toggle (Edwin 2026-07-23: month-scoping cohorts/attribution is semantically fuzzy since a June sample can convert in July). Maintain `periods` in the metrics JSON:
  - `periods.mtd` - recompute EVERY run. Window = 1st of the current month through yesterday (on the 1st of a month, use just that day so far and append "· day 1 partial" to the label). Fields: `name` ("July"), `pill` ("Jul MTD"), `label` ("Jul 1 - 15, 2026 · MTD"), `signups`/`delivered`/`orders`/`revenue` (Klaviyo daily aggregates bucketed to the window), `spend` + per-platform `meta`/`google`/`tiktok` objects `{spend, impr, clicks, ctr, cpm}` (Google gets `conv` instead of cpm) from `client_performance`, `sample_spend` (Step 5a classification over `campaigns_performance` for the window), `paid_signups` (`python scripts/cy_signup_sources.py --start <1st> --end <yesterday>`, take `paid`), and the three per-period section sub-objects `awareness`/`conversion`/`creatives` (see next bullet).
  - **Per-period `awareness` / `conversion` / `creatives` (added 2026-07-23).** Each period carries its own copy of these three blocks, computed for THAT period's window, using the exact same schema and classification rules as the launch-to-date top-level `awareness` / `conversion` / `creatives` blocks documented elsewhere in Step 10 (awareness = per-platform sums over AWARENESS campaigns in the window; conversion = D2C campaigns in the window, so `periods.last` (June) is empty because D2C launched 2026-07-21 and renders the "no campaigns live yet" state; creatives = top/bottom scored by objective within the window). Build each by re-running the same pull/classification you already do for the top-level block, but scoped to the period window. **These are OPTIONAL: if you omit them, the renderer falls back to the top-level launch-to-date block for BOTH periods, which makes the tab read identically under Jun and Jul (exactly the bug Mel reported), so you MUST populate them for the toggle to work.** Keep the top-level `awareness`/`conversion`/`creatives` too (they are the launch-to-date fallback and some non-toggling references still read them).
  - `periods.last` - CARRY OVER unchanged (including its `awareness`/`conversion`/`creatives` sub-objects). Only recompute on the FIRST run of a new month: freeze the just-closed month into `periods.last` (same fields + the three section sub-objects, full-month window) and start a fresh `periods.mtd`. June 2026 was frozen on 2026-07-03; the next recompute is the Aug 1 run (freezing July).
  - Never drop the `periods` key: the renderer falls back to a single launch-to-date pseudo-period and the toggle disappears.
- `sample_spend` = sum of sample-driving campaigns (Step 5a) over the window. `cohorts` = an ARRAY (any length, in order), one object **per SAMPLE SHIPMENT BATCH** (Edwin 2026-06-24 - NOT 8k waves): `{name, window (ship dates, en-dash "–"), delivered, buyers, rev, age_days}`. `delivered` = Strata "mail piece received" (`Ud2PPs`) attributable to that batch; `buyers`/`rev` = sampled buyers among that batch's recipients (Step-10 Shopify×Klaviyo join), `age_days` = today minus ship date. Renderer builds rows: Sample→Buyer = buyers ÷ delivered; `delivered: 0` renders the row as "pending" (use for the queued backlog row). The renderer builds the table from this array - append a batch row each time one ships, no template change.
- `wow` = the trailing-7d-vs-prior-7d raw values that drive the 5 KPI-card week-over-week badges (Edwin 2026-06-29 - "see trends"). **Always exclude today (partial); the two windows are the last 7 COMPLETE days vs the 7 before that.** With today = `T`, recent = `[T-7 .. T-1]`, prior = `[T-14 .. T-8]`. Pull each as a per-day series and bucket, do NOT reuse the 30-day cumulative totals:
  - `signups` = Klaviyo `UxTJ2Z` count per day (`query_metric_aggregates`, interval day, tz America/New_York), summed per window.
  - `delivered` = Klaviyo `Ud2PPs` count per day, summed per window (lumpy - batch ships, so a red delivered badge usually reflects ship timing, not a CVR drop; that's expected).
  - `revenue` = Klaviyo `UzD6xZ` sum_value per day, summed per window.
  - `spend` = HQ `client_performance` total spend. Easiest: one call with `date_start`/`date_end` = the recent window and `compare_to: "previous_period"` returns `totals.current.spend` (recent) and `totals.prior.spend` (prior) in one shot.
  - `sample_spend` = sum of **sample-driving campaigns only** (Step 5a rule: Meta LEADS + Google `[ROI]` + TikTok sample; exclude awareness/TOF/traffic/engagement + Meta SALES retargeting). `campaigns_performance` with `compare_to: "previous_period"` returns per-campaign `current`/`prior` spend in one call - classify each row, then sum current → recent, prior → prior. The renderer derives CPS = `sample_spend ÷ signups` per window, badge inverted (lower = good). Sign-Ups/Delivered/Revenue badges are up=good; Ad Spend is neutral (mute, never red/green).
  - **Engine-node WoW (section 05, Edwin 2026-06-29 "you missed this").** Same recent/prior windows. The `wow` block also carries 4 engine fields; the Delivered node reuses `delivered` above:
    - `postsample_open` = Post-Sample flow `open_rate` per window as a **0-1 ratio** (`get_flow_report`, custom timeframe = each window; flow "Sample: Delivered + Post-Sample CVR" `VESnCz`). Up=good.
    - `return_visits` = post-sample flow `clicks_unique` per window (the two post-sample flows). Up=good.
    - **Retargeting node KPI = CAC, not spend** (Edwin 2026-06-29 - spend alone is vanity). Provide BOTH `rt_spend` AND `rt_orders` per window from `campaigns_performance` (`name_contains: samplerecipients_rt`, `compare_to: previous_period`): `conversions` → orders, `spend` → spend. The renderer derives CAC = spend ÷ orders, badge inverted (lower = good). A window with 0 RT buyers has undefined CAC; if the PRIOR window had 0 buyers the badge shows `n/a WoW` (no CAC to trend against), and if the recent window has 0 buyers the badge is omitted. Also set the cumulative top-level `rt_spend`/`rt_orders` (lifetime since RT launch ~Jun 19) - the node value = cumulative CAC, sub = "Cost per buyer · N buyers · $X spend".
    - `purchases_rev` = weekly sampled-buyer revenue via the Shopify×Klaviyo join (same method as `sampled_buyer_rev` below, but bucketed into each 7d window). Up=good.
    - **Reviews node has NO weekly source** - Judge.me isn't connected (Klaviyo `get_reviews` returns empty; Shopify exposes only a cumulative metafield count). OMIT it from the `wow` block; the renderer emits no badge rather than fabricating one. Flag the gap to Edwin if asked.
- `postsample_open` / `postsample_sent` = "Sample: Delivered + Post-Sample CVR" flow aggregation (open_rate %, delivered). `flows` = 6 rows in FIXED customer-journey order [Sample Quiz Completed, Welcome Email, Sample: Just Shipped, Sample: Delivered + Post-Sample CVR, Abandonment Browse, Abandonment Checkout], each `{sent=delivered, open=open_rate%, visits=clicks_unique, orders=conversions, rev=conversion_value}` from flow_aggregation. (Order = lifecycle sequence, per Kim 2026-06-24.) Exclude "Internal Testing". Renderer derives return-visits = sum of flow visits.
- `email_orders` / `email_revenue` = sum of flow conversions / conversion_value (used for the table totals row). `rt_spend` / `rt_orders` = Meta `samplerecipients_rt_sales*`. `reviews` / `rating` from Shopify above.
- **Funnel "Returned to Site"** = post-sample email clicks: renderer derives it from `flows[2]` (Just Shipped) + `flows[3]` (Delivered+CVR) visits, rate ÷ `delivered`. So flows[2]/[3] MUST stay the two post-sample flows in journey order. (It's a floor - direct returns aren't counted.)
- **Funnel "Purchased" = COMPLETE sample→buyer count** via a Shopify×Klaviyo join (Edwin 2026-06-24), NOT post-sample email conversions. Provide `sampled_buyers` + `sampled_buyer_rev` in the metrics JSON. How to compute:
  1. `mcp__claude_ai_Shopify__graphql_query`: `{ orders(first:100, query:"created_at:>=<window_start>", sortKey:CREATED_AT){ pageInfo{hasNextPage endCursor} nodes{ name createdAt email test cancelledAt displayFinancialStatus totalPriceSet{shopMoney{amount}} shippingAddress{zip city provinceCode} } } }` - paginate on `hasNextPage` with `after:endCursor`. Use the TOP-LEVEL `email`, NOT `customer{email}`: guest checkouts (most DTC orders) have a null customer object, so `customer{email}` silently drops them.
  2. Drop internal/test orders: `test:true`, `cancelledAt` not null, `displayFinancialStatus` REFUNDED/$0, and emails @catyears.com, @byhandbook.com (the dev studio), the founder `jordankfr@gmail.com` (Jordan, cat "Milo").
  3. Batch-match the remaining buyer emails to Klaviyo: `mcp__klaviyo__get_profiles` filter `any(email,[...])` fields `["email","created","properties"]` (split into ≤25-email batches).
  4. A buyer is a **sampled buyer** if their profile shows `signup_source == "pre-launch sample form"` OR `$source == "Sample request quiz"` OR has quiz props (`furthest_step`/`sample_offer`/`cat_1_name`). Buyers with `$source == -50` (Shopify checkout), `"Pop Up 1"` with no quiz props, or no profile = direct (NOT sampled).
  5. `sampled_buyers` = count of sampled buyers; `sampled_buyer_rev` = sum of their order totals. Renderer sets Purchased = `sampled_buyers`, PURCH_VAL = `$<rev> · <n>`, rate ÷ `delivered`. As of 2026-06-24: 22 of 46 real buyers were sampled ($715); 24 direct; ~10 internal excluded.
  6. **Write the raw orders export** to `.claude/_cy_orders_full.json` from the MCP pull above: a JSON list of rows `[order_name, "YYYY-MM-DD", email_lower, is_test_bool, is_cancelled_bool, total_float, zip, city, state]` (zip/city/state from `shippingAddress`, zip sliced to 5), ALL orders (downstream applies exclusions). `is_test` = internal domain/founder emails per step 2; `is_cancelled` = `cancelledAt` set or REFUNDED/$0. This file feeds `cy_cohort_funnel.py` AND the daily-update buyer count.
     (Offline fallback only, if the Shopify connector is down and someone has an Admin token in `.env`: `python scripts/cy_shopify_orders_pull.py` writes the same file. Not used in the normal run.)
     **FAIL LOUD - do not silently freeze this file.** The claude.ai Shopify connector token expires in headless cron runs (observed 7/11, 7/12, 7/16), which is how this export went a week stale to 7/9 while the rest of the dashboard kept updating. If the Shopify pull errors or returns 0 orders, do NOT skip quietly: (a) log `ORDERS-STALE: shopify pull failed, _cy_orders_full.json NOT refreshed (last good <mtime>)`, (b) leave the old file in place (do not truncate), and (c) add that line to the run's final status so the heartbeat/daily-update surfaces it. Never write partial/empty orders. The durable fix is a Shopify Admin API token (read_orders) in a python puller independent of the OAuth connector - flag to Edwin if this keeps recurring.
- **Daily trend series (client call 2026-07-09, Jordan: time-series views).** Set `daily` = one row per COMPLETE day of the pinned window (exclude today): `{date: "YYYY-MM-DD", signups, delivered, orders, revenue, spend, sample_spend}`. signups/delivered/orders/revenue come straight from the Step-2 per-day arrays (`UxTJ2Z`, `Ud2PPs`, `UzD6xZ` count + sum_value). `sample_spend` per day = Step 5b. `spend` per day = the SAME per-day `campaigns_performance` responses summed over ALL campaigns (no extra calls). The renderer draws the six Daily Trends charts from this; a day missing `spend`/`sample_spend` simply drops out of the spend/CPS charts (never fabricate a day).
- **Cohort x freebie-segment build (client call 2026-07-09: cohort splits + freebie toggle).** AFTER the base metrics JSON is written (it needs `quiz_completed`, `delivered`, `sampled_buyers`, `sampled_buyer_rev`, `audience` in place) and AFTER the orders export above, run:
  `python scripts/cy_cohort_funnel.py`
  It reads the authoritative local cohort files (cohort-1 email list, Strata batch-2 export, cohort-2 per-profile source classification), attributes buyers to cohorts by exact email match, writes `scripts/_cy_profile_ledger.csv`, and patches `cohorts_v2` + `segments` into the metrics JSON (these drive the Samples & Cohorts screen and its freebie toggle; cohort-2 freebie counts are EXACT, cohort-1 is the validated-sample estimate - the renderer labels the basis). It also patches an `income` block onto the Cohort 2 row (ClickUp 86baz2met, Jordan 2026-07-16): the delivered slice crossed by household income (premium/genpop/unknown + freebie), exact per profile, buyers exact, denominator = recipients. Drives the "07b / Cohort 2 by income" section. If the script errors, carry over the previous run's `cohorts_v2` + `segments` unchanged and note it in the log; never drop the keys. When a NEW Strata batch ships, add its recipient export to the script's inputs (same pattern as batch 2) before the next run.
- **Tactical plan (client call 2026-07-09: budget plan in the dashboard).** `tactical_plan` = `{"month": "<Month>", "buckets": [{name, planned, actual_mtd, note}]}`. CARRY IT OVER unchanged if present; the renderer shows a "pending the budget breakdown" row while it's absent. Once Edwin's July bucket split (straight-to-purchase funnel / retargeting / awareness) is locked, populate `planned` per bucket and recompute `actual_mtd` each run: awareness = the Step-5a awareness set's MTD spend, retargeting = Meta `samplerecipients_rt*` MTD spend, conversion funnel = the straight-to-purchase campaign(s) MTD spend once launched.
- **Conversion (D2C) block (Conversion tab, added 2026-07-22: client asked to track the direct-to-purchase funnel Débhora launched 7/21).** `conversion` = `{"launched": "Jul 21", "window": "since Jul 21", "days_live": <int>, "campaigns": [...], "ads": [...]}`. `campaigns` = one object per D2C campaign from the Step-5a `D2C_CAMPAIGNS` set, each `{name (clean label e.g. "D2C ASC · Scaling"), raw_name, structure (e.g. "Advantage+ Shopping" / "CBO · interest test"), status ("Active"/"Paused"), spend, impr, clicks, ctr, purchases (=conversions), revenue (=conversion_value)}` over the pinned window. The renderer derives CPA/ROAS/AOV + the rollup KPI cards and total row. `days_live` = today minus 2026-07-21. `ads` = clean creative labels (creator · angle) of the ads live in these campaigns; pull the current ad list from the launch Slack post or `ads_performance` filtered to the D2C campaign ids, and humanize (do NOT dump raw ad names). If `conversion` is absent/empty the tab renders a "no direct-to-purchase campaigns live yet" state, so never drop the key once launched; carry the last-good campaigns over only if the HQ pull errors, and note it in the log.
- **Creative Scoreboard block (Creative tab, section 13, ClickUp 86baz2met part 3: top/bottom creative from the HQ Creative Hub).** `creatives` = `{"window": "last 30 days", "note": "...", "dna": "...", "top": [3 cards], "bottom": [2 cards]}`. Build it from `top_creatives` (client "Cat Years", the pinned window, per platform - meta + tiktok; it carries the AI hook/format tags + video engagement metrics) with `ads_performance` as the poster/CTR/purchase source (already pulled in Step 5). **Score by OBJECTIVE, never one global metric** (Edwin: the account is mostly awareness video right now, so ROAS ranks noise): awareness/TOF video (Meta `OUTCOME_AWARENESS`, TikTok tof/videoviews) is scored on watch-through (`hook_rate` + `hold_rate`/6-sec view); D2C sales (Meta `OUTCOME_SALES` `d2c*`) on `ctr` + purchases/ROAS. Apply a spend + impression floor (roughly >= $50 and >= 3,000 impr) so a tiny test can't rank top or bottom. Each card = `{label (humanized creator/angle, NEVER the raw ad name), channel (e.g. "Meta · D2C"), format ("UGC video"/"Animation"/"Static"/"Video"), metric_label, metric, sub (2-3 supporting stats + spend), thumb, link}`. `thumb`: Meta `poster_url` is a relative path -> prefix `https://hq.jetfuel.agency/storage/`; TikTok `poster_url` is already absolute. `link`: `get_ad_share_url` (platform "meta"/"tiktok", `ad_fb_ids` = the ad's `fb_id`); omit (empty string) if unavailable. `dna` = the one-line winning pattern (hook/format/angle that separates), from `creative_tag_analytics` or the tag rollup. If the creative pull errors, carry over the previous run's `creatives` block and note it in the log; the renderer shows a "refreshes next pull" placeholder if the key is absent, so never drop it once seeded. (`top_creatives` + `get_ad_share_url` were added to the bat's `--allowedTools` 2026-07-22.)
- The engine Return-Visits node = post-sample clicks; Purchases node = `sampled_buyers`. The flow table's "All email flows" total row is the broader all-flows sum.

**Cohorts = sample SHIPMENT BATCHES** (Edwin 2026-06-24; the earlier "~8k waves" was a wrong extrapolation from his "first 8k is cohort 1" example - do NOT use fixed-size waves). One row per Strata mailing batch. Identify batches from Strata "mail piece sent" (`T7vkvz`) clusters and their "mail piece received" (`Ud2PPs`) deliveries. **Caveat:** `T7vkvz` currently undercounts (broken webhook, received > sent - see the Strata note in [[feedback_cat_years_dashboard]]), so only the launch batch is cleanly identifiable today. Until that feed is fixed, use: row 1 = **Batch 1 · Launch** (shipped ~Jun 13–14, delivered = total `Ud2PPs` to date ≈ 7,507), then one **"Awaiting shipment"** row with `delivered: 0` and `window` = "<backlog> sign-ups queued" (backlog = sign-ups − delivered). Per-batch `buyers`/`rev` = Step-10 sampled buyers whose Klaviyo sign-up falls in that batch's recipient wave (launch batch ≈ pre-Jun-10 sign-ups). When the sent feed is fixed, split real batches and add a row each. If rows exceed ~7, keep recent 6 + an "Earlier batches" summary.

**Render + reshare:**
1. `python scripts/cat_years_dashboard_render.py scripts/_cat_years_dashboard_metrics.json .claude/cat-years-dashboard.html` - it warns on unreplaced tokens; if it warns, fix the JSON, do NOT upload a broken file.
2. Mint an upload URL: `mcp__claude_ai_jetfuel_hq__update_page` with `id: 15, upload: true`.
3. Upload: `curl -s -X POST -H "Content-Type: text/html" --data-binary @.claude/cat-years-dashboard.html "<upload_url>"`. Confirm the response shows an incremented `version` and `byte_size` near 105-110KB (v2 multi-screen dashboard, inline SVG charts + per-point hover-tooltip data added 2026-07-16 for Jordan; the D2C Conversion tab added 2026-07-22 pushed it to ~108KB; the Cohort-2-by-income section + Creative Scoreboard added 2026-07-22 pushed it to ~117KB; was ~85KB before the charts, ~40KB before 2026-07-09). A sudden drop back to ~40KB means the template regressed. Add a line to the Step 9 log: `Client HTML reshared: page 15 vN (B bytes)`.

Always UPDATE id 15 (never create a new page) so the share URL stays stable. If `list_pages client="Cat Years"` shows no id 15, recreate via `create_page` (title "Cat Years - Launch Performance Report", slug "cat-years-launch-report", expires_at "never", client "Cat Years") and record the new id in `feedback_cat_years_dashboard.md`.

## Exec Summary template

Lines 1-42 of the Exec Summary tab, with `{placeholders}` replaced by computed values. The structure is fixed; only the numbers and context strings change.

```
Row 1:  "CAT YEARS DASHBOARD" | "" | ""
Row 2:  "Snapshot: {today} ({days_since_launch}). Window: last 30 days." | "" | ""
Row 3:  (blank)
Row 4:  "HEADLINE NUMBERS" | "" | ""
Row 5:  "Leads (Quiz Completed)" | "{period_leads:,}" | "30-day total"
Row 6:  "  · Today alone" | "{today_leads:,}" | "{pct_today}% of period leads"
Row 7:  "  · Launch day (2026-06-08)" | "{launch_day_leads}" | ""
Row 8:  "Samples shipped via Strata" | "{samples_shipped}" | "{pct_of_leads}% of leads - {bottleneck_status}"
Row 9:  "Shopify revenue" | "${revenue:,.2f}" | "{orders} orders, AOV ${aov:,.2f} (via Klaviyo Placed Order)"
Row 10: "Checkouts started" | "{checkouts}" | "Checkout-to-Order rate: {co_pct}%"
Row 11: "Total ad spend" | "${spend:,.2f}" | "30-day total"
Row 12: "CPS (sample-driving campaigns)" | "${cps_sample_period:.2f} period / ${cps_sample_7d:.2f} last 7d" | "Conv-optimized spend only (Meta LEADS + Google [ROI] + TikTok sample). {trend_note: e.g. 'Trending UP from $X to $Y' if rolling rising}"
Row 13: "CPS (blended, all spend incl awareness)" | "${cps_blended:.2f}" | "Context only. ~{awareness_pct}% of period spend is awareness/TOF, excluded from sample CPS above"
Row 14: (blank)
Row 15: "AD SPEND BY CHANNEL" | "" | ""
Row 16: "Meta (Facebook)" | "${meta_spend:,.2f} ({meta_pct}%)" | "{meta_imp:,} imp, {meta_clicks} clicks"
Row 17: "TikTok" | "${tt_spend:,.2f} ({tt_pct}%)" | "{tt_imp:,} imp, {tt_clicks} clicks"
Row 18: "Google Ads" | "${g_spend:,.2f} ({g_pct}%)" | "{g_clicks} clicks, {g_conv} conv, ${g_rev:,.2f} rev"
Row 19: (blank)
Row 20: "FUNNEL HEALTH" | "" | ""
Row 21: "Quiz Started -> Quiz Completed" | "{qsqc_pct}%" | "{qs:,} -> {qc:,}"
Row 22: "Quiz Completed -> Samples shipped (Strata)" | "{qcms_pct}%" | "{ms} of {qc:,}"
Row 23: "Checkouts -> Orders" | "{co_pct}%" | "{orders} of {checkouts}"
Row 24: "Orders / Spend ratio" | "{os_ratio}x" | ""
Row 25: (blank)
Row 26: "TOP CREATIVES (Meta, by performance)" | "" | ""
Row 27-30: top 4 creatives by CTR/spend mix (see Step 6 dedupe logic)
Row 31: (blank)
Row 32: "ISSUES TO FIX" | "" | ""
Row 33-36: detected issues. Static + dynamic. Default to the 4 known: Strata bottleneck, broken UTM template, missing Klaviyo props, no per-channel LPs. If Strata mail_sent / quiz_completes ratio > 50%, swap "Strata pipeline backed up" for "Strata pipeline healthy".
Row 37: "WATCH NEXT" | "" | ""
Row 38-42: forward-looking metrics (Strata volume, sample->purchase cohort, CPS at scale, offer_group, anything new)
```

## What NOT to do

- Do NOT add new tabs. If the structure needs to change, do it in a manual session.
- Do NOT touch Targets, Pre-Launch Audit, UTM Reference, or Sample-to-Buyer Cohort tabs - those are manually maintained.
- Do NOT write to Shopify directly. Klaviyo's Placed Order metric IS the Shopify revenue (via Klaviyo's Shopify integration).
- Do NOT call `ToolSearch` for tool schemas you can name explicitly - every search costs quota. The allowed-tool list in the bat file gates everything you need.
- Do NOT post to Slack. This is silent telemetry. If a tool fails, log it; the next session will catch it.
