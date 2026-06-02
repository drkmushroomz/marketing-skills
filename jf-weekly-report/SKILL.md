---
name: jf-weekly-report
description: "Jetfuel weekly Meta performance briefing. Pulls last 7 days of Meta data per client from HQ, compares to prior 7 days, applies client-specific target CPA/ROAS goals, scores against the Andromeda 14-point rubric, generates a per-client Slack-formatted summary plus a detailed markdown report. Use when the user says 'weekly report', 'pull the weekly', 'how did clients do last week', 'Monday briefing', or schedule it as a 7AM Monday cron."
disable-model-invocation: true
---

# /jf-weekly-report — Weekly Meta Briefing (Jetfuel)

Monday-morning automated briefing for every active JF Meta client. Pulls last 7 days, compares to prior 7, applies per-client goals from HQ, and assesses each account on both performance and Andromeda compliance. Posts a concise summary to each client's mapped Slack channel and a full detail report to the JF strategist console.

## Arguments

- `--client name` — single client. Default: all active clients with Meta.
- `--date-range` — Default: last_7d. Supports `last_7d`, `last_14d`, `custom:YYYY-MM-DD:YYYY-MM-DD`.
- `--compare` — Default: previous_7d. Supports `previous_7d`, `previous_4w_avg`, `previous_year`.
- `--top-n N` — Top winners/losers to highlight. Default: 3.
- `--format slack|markdown|both` — Default: both.
- `--dry-run` — Generate reports, don't post to Slack.

## Steps

### 1. Load identity, client roster, config

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-weekly-report/config.json` for client target ROAS/CPA, Slack channel mapping.
- `list_clients(active_only=true)` → roster filtered to clients with Meta platform via `get_client_platforms`.

### 2. Per client, pull weekly performance from HQ

For each Meta client:

```
client_performance(client_id={...}, date_start, date_end, platform_filter="meta")
campaigns_performance(platform_id={meta_platform}, date_start, date_end, compare_to="previous_period")
get_platform_insights(platform_id={...}, date_start, date_end, compare_to="previous_period")
```

Returns: spend, conversions, conversion_value, ROAS, CPA, CTR, CPM, frequency, impressions for both periods.

### 3. Pull goals from HQ

```
get_client_goals(client_id={...})
```

Extract: target_roas, target_cpa, monthly_revenue_goal, monthly_spend_cap.

If HQ doesn't have a goal set: fall back to config override; if still missing, flag "no goal set — using account avg as benchmark."

### 4. Classify account health

For each client:

- 🟢 **GREEN**: ROAS ≥ target AND CPA ≤ target AND no metric declined >10% WoW
- 🟡 **YELLOW**: any one metric declined 10-20% WoW, or ROAS within 10% of target floor
- 🔴 **RED**: ROAS below target, OR CPA >20% above target, OR a metric crashed >20% WoW

### 5. Apply Andromeda 14-point check

Pull the data needed for the rubric from `project_andromeda_audit_rubric.md`:

- **Pillar 1 (Structure)**: 70%+ in ASC? Retargeting layer present? Sandbox running? No lookalikes? — from `campaigns_performance`
- **Pillar 2 (Signal)**: CAPI on? EMQ ≥7? — from Meta MCP pixel diagnostics
- **Pillar 3 (Volume)**: Active ad count meeting formula? 3+ new concepts launched this month? Pruning cadence? — from `top_creatives`, `compare_creative_periods`, `list_creative_ads`
- **Pillar 4 (Diversity)**: 6+ themes? 3+ tones? 3+ formats? — from `creative_tag_analytics` + ad name parsing

Score 0-14 per client. Note: Pillar 4 is approximate if naming convention isn't fully adopted.

### 6. Identify top + bottom performers

Per client:
```
top_creatives(platform_id={...}, limit={top-n}, sort="roas")
```

Plus bottom: query `ads_performance` sorted ascending on ROAS, filtered to `--min-spend 100`.

### 7. Generate three actions per client

Based on the data, output three recommended actions, each must reference specific campaign/ad names or metric values:

- One on **budget allocation** (likely sourced from `/jf-rebalance` recommendations)
- One on **creative** (likely from `/jf-fatigue-scan` if fatigue is detected)
- One on **architecture** (likely from `/jf-meta-audience-audit` findings, esp. if Andromeda score is <10)

### 8. Resolve Slack channels

`list_slack_channels()` → match client name → cache to config.

### 9. Build per-client Slack message

Use `mcp__claude_ai_Slack__slack_send_message`. Format:

```
📊 Weekly Meta — {Client} — w/c {date}

Status: 🟡 YELLOW
ROAS: 2.3x (-0.4 WoW) | CPA: $42 (+$6) | Spend: $5,420 (+$320) | Freq: 3.1
Purchases: 129 (-22) | CPM: $32 (+$4)

Andromeda: 8/14
- Pillar 1: 3/4 (✅ ASC, ✅ Retargeting, ✅ Sandbox, ❌ found 1 LAL ad set)
- Pillar 2: 2/3 (✅ CAPI, ❌ EMQ 6.8 — below floor)
- Pillar 3: 2/3 (✅ ad count, ✅ pruning, ❌ only 1 new concept this month)
- Pillar 4: 1/4 (❌ Inspired tone at 68%, ❌ only 4 themes, ✅ 4 formats, ❌ no founder-led)

Top 3 winners (ROAS):
1. HamptonWater_Worried_FrequentTraveler_BOFU_UGC_v04 — 4.8x
2. HamptonWater_Amused_BusyParent_TOFU_Reels_v02 — 4.1x
3. HamptonWater_Assured_LuxuryRose_MOFU_Founder_v01 — 3.6x

Bottom 3 (>$100 spend):
1. HamptonWater_Inspired_Generic_TOFU_Static_v07 — 0.4x
2. HamptonWater_Inspired_Generic_TOFU_Static_v05 — 0.6x
3. (note: same tone+persona pattern across losers — fatigue signal)

Three actions for this week:
1. Pause LAL prospecting ad set "LAL_1pct_Purchase" ($840/wk wasted). Redirect to Scale ASC.
2. Replace 3 underperforming Inspired statics with 3 Worried UGC briefs (/jf-bulk-creative ready).
3. Triage EMQ — Aimerce config check, expected to land 8.5+.

Reports: [Sheet link] [Markdown link]
— crew version: {git hash}
```

### 10. Generate the detail markdown

`.claude/ops/jf-weekly-report/reports/{client}-{date}.md` — full metric table (all campaigns, all metrics WoW), creative performance table (all active ads sorted by ROAS), Andromeda scoring detail, action rationale.

Also output a roll-up sheet via `mcp__google-workspace__create_spreadsheet` with one tab per client + a strategist roll-up tab.

### 11. Strategist console summary

Print to conversation, aggregated across all clients:

```
JF Weekly Roll-up — w/c {date}

Status: 8 clients GREEN, 5 YELLOW, 1 RED
Spend across roster: $X (vs $Y prior week, {pct}%)
Andromeda avg score: 9.2/14
RED clients needing immediate review: {DeLille}
- Reason: ROAS dropped 30% WoW after creative refresh stalled

Top 3 actions for the week (strategist-priority):
1. DeLille — emergency creative refresh ({n} fatigue flags)
2. Hampton Water — kill LAL prospecting, EMQ triage
3. Grip Studs — Andromeda audit (12/14 — keep doing what they're doing)

Per-client Slack alerts: posted to {n} channels.
Detail reports: {sheet links}
```

## Important Rules

- **Per-client goals from HQ, never global.** Always pull `get_client_goals`.
- **Andromeda score is the second story.** Don't bury it. A client with great ROAS but 5/14 Andromeda is one creative refresh away from a crash.
- **Three actions, each with specific evidence.** No vague "improve creative." Cite the ad name, the metric, the dollar amount.
- **Slack channel per client.** Never blast all client data to JF internal channel — use the client-mapped channel.
- **No fabricated data.** If HQ doesn't have an EMQ reading, label "N/A — check Events Manager manually." Never estimate.
- **Crew version in every Slack post** (per CLAUDE.md global rule on communications about bugs/issues; weekly reports trigger feedback often).
- **Display all times in user's timezone.** Default 7AM Monday local.
- **Dry-run for testing.** Don't blast Slack accidentally — `--dry-run` writes the reports and prints what would post.

## Config

`.claude/ops/jf-weekly-report/config.json`:

```json
{
  "defaults": {
    "date_range": "last_7d",
    "compare": "previous_7d",
    "top_n": 3,
    "min_spend_for_creative_ranking": 100,
    "internal_strategist_channel": "#jf-paid-ops"
  },
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "meta_platform_id": null,
      "slack_channel": "#hamptonwater-insights",
      "target_roas": 2.5,
      "target_cpa_usd": 35,
      "monthly_spend_cap_usd": 24000,
      "report_emq_inline": true
    },
    "grip-studs": {
      "hq_client_id": 30,
      "slack_channel": "#gripstuds-paid",
      "target_roas": 3.0,
      "target_cpa_usd": 28
    }
  }
}
```

## Scheduling

Per `feedback_local_cron.md` — Windows Task Scheduler, NOT cloud cron. Recommended: Monday 7AM PT.

Example task: `claude code -p "/jf-weekly-report"` once weekly.

## Why this skill exists

External `/weekly-report` pulls metrics and emails a table. The Jetfuel version anchors everything in per-client HQ goals (so a 2.3x ROAS is GREEN for a wine client and RED for a supplement), layers the Andromeda 14-point check (so a client with great metrics but a creative engine about to crash gets flagged), and routes each report to the client-specific Slack channel (not a generic firehose). It's the Monday-morning deliverable that should land before the strategist opens their laptop.
