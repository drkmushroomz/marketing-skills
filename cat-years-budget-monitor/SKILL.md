---
name: cat-years-budget-monitor
description: Daily cron check of the Cat Years "Drinking Problem" campaigns. Reads pre-collected Google facts, fills in Meta spend from jetfuel-hq, and writes a Slack alert file ONLY if a campaign's spend went over budget. The wrapper posts it.
---

# Cat Years Budget Monitor

All scheduled jobs run locally via Windows Task Scheduler. The wrapper
`scripts/cat_years_budget_monitor.ps1` already ran `cat_years_budget_monitor.py --collect`,
so **Google spend + all budgets are already collected** at
`scripts/_cat_years_budget_facts.json`.

Your job is narrow: **read facts -> get Meta spend -> decide breaches -> Write the
alert text to `scripts/_cat_years_budget_alert.txt` ONLY if something breached ->
stop.** The wrapper posts the file (and posts nothing if you leave it empty).

Do NOT post to Slack yourself. Do NOT change budgets. Do NOT re-pull Google data.

## The rule

A campaign **breaches** when yesterday's spend > `threshold_pct`% of its daily budget
(default 120%). Google Ads legitimately spends up to ~2x its daily cap on a given
day and averages out over the month, which is why the threshold is above 100%.
Meta ad sets can also run up to ~25% over on a single day as normal pacing — note
that in the message if a Meta breach is only marginal.

## Step 1 — Read the facts

`Read scripts/_cat_years_budget_facts.json`. Shape:

```json
{
  "yesterday": "YYYY-MM-DD",
  "threshold_pct": 120,
  "channel": "C0B4L6NSCBY",
  "google": [
    {"platform":"Google","id":"...","name":"...","spend":70.21,"budget":100.50,"over_pct":69.9,"breach":false},
    ...
  ],
  "meta": {"platform":"Meta","hq_campaign_id":2877,"name":"jf_tof-...","budget":210.0,"spend":null}
}
```

The `google[*].breach` flags are already computed by Python — trust them.

## Step 2 — Get Meta spend for `yesterday`

If `mcp__claude_ai_jetfuel_hq__campaigns_performance` isn't visible, first call
`mcp__claude_ai_jetfuel_hq__load_ads_tools`.

Call `mcp__claude_ai_jetfuel_hq__get_campaign_insights` with
`campaign_id: 2877`, `platform_type: "meta"`, `date_start` = `date_end` = `yesterday`.
Take the campaign's total spend for that single day. (Fallback: `campaigns_performance`
with `client: "Cat Years"`, that date, `name_contains: "herovideo"`.)

Compute for Meta:
- `over_pct = meta.spend / meta.budget * 100`
- `breach = meta.spend > (threshold_pct/100) * meta.budget`

## Step 3 — Decide

Collect every campaign where `breach` is true (the Google ones from facts + Meta if it breached).

- **No breaches:** Write an **empty** file to `scripts/_cat_years_budget_alert.txt`
  (just write `""`). Then stop. The wrapper posts nothing. This is the normal daily outcome.
- **One or more breaches:** build the Slack message in Step 4 and Write it to that file.

## Step 4 — Build the alert (only if breaches)

Slack `mrkdwn`. Keep it tight. Template:

```
*:rotating_light: Cat Years budget alert — {yesterday}*
These "Drinking Problem" campaigns spent over {threshold_pct}% of daily budget yesterday:

:warning: *{platform}* `{short name}`
   spent *${spend}* vs *${budget}*/day budget  ({over_pct}% of budget)

{repeat per breaching campaign}

_Google can flex up to ~2x daily and averages out over the month; Meta up to ~25%/day. Check before cutting._
crew version: {crew_version}
```

For `{short name}` use a readable label, e.g. "Video Views (Google)", "Hero TVC (Google)",
or "Hero Video TOF (Meta)". Get `{crew_version}` from `git rev-parse --short HEAD` via Bash
(or reuse what the prompt passed in).

## Step 5 — Write the file

Use the Write tool to save the message (or empty string) to
`scripts/_cat_years_budget_alert.txt`. You are NOT responsible for the Slack call.

## What NOT to do

- Do not post to Slack, change budgets, or touch any campaign.
- Do not re-pull or recompute the Google numbers — Python already did.
- Do not spawn subagents or use ToolSearch — keep it to ~4 tool calls (1 Read, 1 HQ
  load + 1 HQ insights, 1 Write; +1 Bash for version if needed).
- Do not write a non-empty file when nothing breached — that would post a false alarm.
