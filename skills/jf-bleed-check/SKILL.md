---
name: jf-bleed-check
description: "Detect budget bleed across all JF Meta clients — ad sets spending above the client-specific threshold with zero or insufficient conversions in the last N hours. Identifies bleed, posts to the client's #insights Slack channel (mapped via HQ list_slack_channels), logs the incident, and recommends action without auto-pausing. Use when the user says 'check for bleed', 'any ad sets bleeding', 'budget check', 'morning safety scan', or as a scheduled 4-6h sweep."
disable-model-invocation: true
---

# /jf-bleed-check — Budget Bleed Detector (Jetfuel)

Sweeps every active JF Meta client in HQ, pulls the last N hours of spend + conversion data, and surfaces ad sets that are bleeding budget against the client's specific target — not a global $50 default. Posts to the client's mapped Slack channel and writes an audit log.

**This skill does NOT auto-pause.** Per `feedback_no_pause_client_spend.md`, we never pause client spend without explicit human sign-off. Bleed-check flags, alerts, and recommends — humans pause.

## What "bleed" means at Jetfuel

A bleeding ad set is one where:
- Spend in the last `--window-hours` exceeds `target_cpa × bleed_multiplier` (default multiplier: 2.5×)
- AND conversions in that same window are below `bleed_floor` (default: 0)
- AND the ad set is not in its first 24h of learning (which Meta's algorithm rightfully spends to find data)

The threshold is **per-client**, not global. A Hampton Water bleed threshold is different from a Grip Studs threshold because their target CPAs differ. Pull thresholds from HQ client goals where possible.

## Arguments

- `--client name` — single client. Default: all active clients.
- `--window-hours N` — lookback. Default: 6.
- `--bleed-multiplier X` — spend ÷ target_cpa to trigger. Default: 2.5.
- `--bleed-floor N` — conversion count at or below which we flag. Default: 0.
- `--alert mode` — `slack` (default), `console`, `both`, `none`.
- `--dry-run` — flag bleed but don't post Slack alerts.

## Steps

### 1. Load identity, config, client roster

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-bleed-check/config.json` for per-client overrides + Slack channel mapping.
- `list_clients(active_only=true)` → roster.
- For each client: `get_client_platforms(client_id)` → find Meta platform_id.
- For each client: `get_client_goals(client_id)` → extract target_cpa, target_roas if set in HQ. Fall back to config overrides if HQ goals are blank.

### 2. Pull last N hours of ad set performance per client

Per client Meta platform:
```
ad_sets_performance(
  platform_id={meta_platform_id},
  date_start={now - window_hours},
  date_end={now},
  status_filter="ACTIVE"
)
```

This returns spend, impressions, clicks, conversions, conversion_value, roas, cpa per ad set.

If HQ's `ad_sets_performance` doesn't expose hour-grain, fall back to Meta MCP:
```
mcp__meta__meta_list_adsets(account_id, status="ACTIVE")
mcp__meta__meta_get_insights(level="adset", time_range={since: now-Nh, until: now})
```

### 3. Apply per-client bleed rules

For each ad set, compute:
- `target_cpa` (from HQ goals OR client config OR account avg ROAS-back-solve)
- `bleed_threshold = target_cpa × bleed_multiplier`
- `bleeding = spend > bleed_threshold AND conversions <= bleed_floor AND age_hours > 24`

Edge cases:
- **First 24h of learning phase** — exempt unless spend > 5× target CPA.
- **Brand campaigns with no CPA target** — use $X cap from config; if no cap, flag as "no goal set" and warn.
- **CBO ad sets** — bleed analyzed at campaign level, not ad set (Meta MCP returns ad-set-level even under CBO, but the lever is the campaign).
- **Sandbox campaigns** — multiplier auto-relaxes to 4× (sandbox is allowed to lose, that's the point).

### 4. Sort + classify

Per bleeding ad set, classify:
- 🔴 **Critical**: spend > 5× target_cpa, no conversions, >48h old.
- 🟠 **High**: 2.5–5× target_cpa, no conversions.
- 🟡 **Watch**: 2.5× threshold met but has 1 conversion (not full bleed but underperforming).

### 5. Resolve the Slack channel per client

`list_slack_channels()` → match client name to channel (typically `#client-{slug}-insights` or `#client-{slug}-paid`). Cache to config on first match.

### 6. Post the alert (unless `--dry-run`)

For each client with bleed, use `mcp__claude_ai_Slack__slack_send_message` to post to the client's channel:

```
🩸 Bleed check — last {window}h — {client name}

🔴 Critical ({n})
• {Adset name} — spent ${X} (target ${cpa}, threshold ${threshold}) — 0 conv
  [Ads Manager link]

🟠 High ({n})
• ...

Recommended action:
1. Review ASAP — these are spending without performance.
2. Common causes: bad creative match, broken landing, frequency cap blown, audience saturation.
3. Decisions: pause / cut budget 50% / swap creative / let it run if pre-launch data.

This is an alert, not an auto-action. Nothing has been paused.
— crew version: {git hash}
```

If no bleed: post a brief "✅ {client} clear — checked {n} ad sets" only to the JF internal #ops channel, not the client channel (no spam).

### 7. Write the audit log

`.claude/ops/jf-bleed-check/logs/{YYYY-MM-DD}.jsonl` — one line per check, one client per line:
```json
{"ts":"...","client":"hampton-water","window_h":6,"adsets_checked":12,"bleeding":[{"adset_id":"...","name":"...","spend":425,"target_cpa":35,"conv":0,"severity":"critical"}]}
```

### 8. Present in-conversation summary

```
Bleed check ({window}h):
- Hampton Water: 🟠 2 high — $612 bleeding across "JF_Sandbox_Test_3" and "JF_Scale_ASC". Alert posted.
- Grip Studs: 🟢 clear
- DeLille: 🔴 1 critical — "Vineyard_BOFU_v3" — $1,140 in 6h, 0 purchases. Alert posted.
- ...

Total bleed across roster: $X / 6h ({n} ad sets across {n} clients).
Nothing paused. Strategist review required.
```

## Important Rules

- **NEVER auto-pause.** Per `feedback_no_pause_client_spend.md`. This skill alerts only.
- **Per-client thresholds.** Never hardcode a $50 global default — always derive from HQ goals or client config.
- **Sandbox carve-out.** Sandbox campaigns expect to lose; multiply threshold by 4× for any campaign matching `JF_Sandbox_*` or tagged sandbox in config.
- **First 24h learning exemption.** Don't flag fresh ad sets unless spend is 5×+ off — Meta needs runway.
- **Slack channel resolution is config-cached.** Resolve once, save to config. If a client doesn't have a mapped channel, post to JF internal #ops with the client name in the message.
- **Bleed alert includes the crew version** (per CLAUDE.md rule on bug/issue communications, and bleed alerts often spawn bug investigations).
- **Audit log is append-only.** Never overwrite a day's log; one file per UTC date.
- **Display all times in user's timezone** in conversational output (but log in UTC).

## Config

`.claude/ops/jf-bleed-check/config.json`:

```json
{
  "defaults": {
    "window_hours": 6,
    "bleed_multiplier": 2.5,
    "bleed_floor": 0,
    "sandbox_multiplier_override": 4.0
  },
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "target_cpa_usd": 35,
      "slack_channel": "#hamptonwater-insights",
      "sandbox_pattern": "JF_Sandbox_*"
    },
    "grip-studs": {
      "hq_client_id": 30,
      "target_cpa_usd": 28,
      "slack_channel": "#gripstuds-paid"
    }
  },
  "internal_ops_channel": "#jf-ops-alerts"
}
```

## Scheduling

Per `feedback_local_cron.md` — schedule this skill via **Windows Task Scheduler**, not cloud cron (the 3-session limit silently drops runs). Recommended cadence: every 6h during business hours.

Example task: `claude code -p "/jf-bleed-check"` 4× daily.

## Why this skill exists

The generic `/bleed-check` hardcodes a $50 threshold and auto-pauses. Both are wrong for Jetfuel:
1. **Thresholds aren't global.** A wine brand with $80 AOV has a very different bleed threshold than a $20 supplement.
2. **We don't auto-pause client spend.** Per `feedback_no_pause_client_spend.md`. Pausing without context can kill a launch in its learning phase, or pause a brand awareness push that's working on view-through metrics not tracked here.

The Jetfuel version respects per-client goals from HQ, applies sandbox carve-outs, and treats itself as a strategist alert, not an autopilot.
