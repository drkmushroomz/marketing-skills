---
name: jf-fatigue-scan
description: "Jetfuel creative fatigue detector. Pulls ad-level performance for a JF client over a rolling window, classifies fatigue using both performance trend AND emotional/messaging diversity (the actual root cause per the JF playbook), and generates replacement briefs across the 4-tone matrix. Use when the user says 'check for fatigue', 'fatigue scan', 'are our ads dying', 'what should we replace', 'creative refresh', 'CPM is climbing', 'frequency too high'."
disable-model-invocation: true
---

# /jf-fatigue-scan — Creative Fatigue Scan (Jetfuel)

Find fatiguing creatives across a JF Meta client account. Unlike the generic `/fatigue-scan` that watches hook-rate + frequency in isolation, the Jetfuel version diagnoses **the actual cause** — emotional monotony or theme over-concentration — because per `blog-drafts/05-emotional-creative-fatigue.md`, "your ads aren't fatiguing because they look the same. They feel the same."

## Two-layer fatigue detection

**Layer 1 — Performance signals** (per-ad metrics over rolling window)
- CTR WoW decline > 15%
- CPM WoW increase > 30%
- Frequency > 4.0
- Hook rate (video thru-play / impressions) below client floor

**Layer 2 — Diversity signals** (account-level, the JF differentiator)
- Single emotional tone covers >50% of active ad spend (`05-emotional-creative-fatigue.md`)
- Single messaging theme covers >40% of active ads (Andromeda compression risk)
- <3 of 4 tones represented in active set
- <6 of 12 messaging themes represented in active set
- Format mix dominated by one type (e.g. all static)

Layer 2 is what most fatigue scanners miss. Edwin on the podcast: "If all of your ads are sort of a single tonality type of ad and it's 100% inspiration, then that's where the element of fatigue comes in. Like, oh, I kind of seen the same story over and over."

## Arguments

- Client name. Default: ask.
- `--lookback N` — days of data. Default: 14.
- `--min-spend USD` — minimum lifetime spend to be in scope. Default: 100.
- `--ctr-decline 0.15` — WoW CTR decline threshold.
- `--frequency-cap 4.0` — frequency threshold.
- `--hook-rate-floor 0.25` — hook rate floor (videos only).
- `--include-paused` — also analyze paused ads for retrospective lessons.

## Steps

### 1. Load identity, client context, naming convention

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-fatigue-scan/config.json` for client overrides + ad-set spend floors.
- Read `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md` for current target CPA, founder availability, asset library.
- The skill assumes the JF naming convention `{Client}_{Tone}_{Persona}_{Funnel}_{Format}_v{NN}` is in use. If ads don't match this pattern, we'll still do Layer 1 — but Layer 2 needs the conventions to slice by tone/theme/persona. If naming is missing, surface that as the FIRST recommendation.

### 2. Pull active ad performance per client Meta platform

```
get_client_platforms(client_id) → meta_platform_id
ads_performance(
  platform_id={meta_platform_id},
  date_start={now-lookback},
  date_end={now},
  status_filter=active_only ? "ACTIVE" : "ALL"
)
```

For each ad: spend, impressions, clicks, conversions, frequency, cpm, ctr, video_thru_play (if video), date_start, age_days, naming_convention_parts (parsed from ad name).

### 3. Layer 1 — Per-ad performance fatigue

For ads with >= `--min-spend`:

Compute week 1 vs week 2 daily averages. Flag:
- 🔴 **HIGH RISK**: CTR W2 < W1 × (1 - ctr-decline) AND frequency > cap, OR CPM W2 > W1 × 1.3, OR hook rate W2 < floor.
- 🟡 **MEDIUM RISK**: any one of those breached, but not multiple.
- 🟢 **HEALTHY**: stable or improving.

Per `blog-drafts/01-creative-production-formula.md`, the natural win rate is 25–35%, so expecting 100% healthy is wrong. The signal is *trend*, not absolute pass/fail.

### 4. Layer 2 — Account-level diversity diagnosis

Parse all active ad names via the JF naming convention. Build:

```
Tone distribution: Assured 12%, Worried 7%, Inspired 68%, Amused 13%
Theme distribution: Founder Story 41%, Social Proof 22%, ...
Format mix: UGC 18%, Founder 12%, Static 55%, ...
Funnel coverage: TOFU 30%, MOFU 15%, BOFU 55%
```

Apply JF rules from `project_andromeda_audit_rubric.md`:
- Tone diversity: ≥3 of 4 tones, no single tone >50% → **FAIL: Inspired at 68% means emotional monotony.**
- Theme diversity: ≥6 of 12 themes covered → flag if below.
- Format mix: ≥3 formats, with founder-led OR UGC present in the mix.
- Funnel coverage: all 3 stages present.

### 5. Pull the JF monthly creative volume target

If `.claude/ops/jf-bulk-creative/manifests/` has historical data for this client, compute the current monthly fresh-ad count and compare against the formula:

```
needed_monthly_ads = (monthly_budget / target_cpa × target_winners_simultaneous) 
                  ÷ (avg_winner_lifespan_days × win_rate)
```

Per `01-creative-production-formula.md`. If under target → flag as a volume issue, not just a fatigue issue.

### 6. Cross-reference HQ creative analytics

```
creative_summary(platform_id={...}, date_start={...}, date_end={...})
top_creatives(platform_id={...}, limit=20)
compare_creative_periods(platform_id={...}, current_window, prior_window)
creative_tag_analytics(platform_id={...})  # if creative tags are populated
```

This gives the team's perspective on what tags/themes are winning vs the manual ad-name parse.

### 7. Generate the fatigue report

Write `.claude/ops/jf-fatigue-scan/reports/{client}-{YYYY-MM-DD}.md`:

```
# /jf-fatigue-scan — {Client} — {date}

## TL;DR
- {N} ads analyzed, {n_high} HIGH risk, {n_med} MEDIUM risk.
- Diversity score: {x}/4 (tone {t}, theme {th}, format {f}, funnel {fn})
- Monthly creative volume: {actual} vs target {needed} → {OK / SHORT}.
- ROOT CAUSE: {emotional monotony | theme over-concentration | volume shortfall | true creative decay}

## High-risk ads (table)
| Ad name | Tone | Theme | Spend | CTR Δ | Freq | CPM Δ | Verdict |

## Diversity diagnosis
Tone distribution: {pie}
Theme distribution: {bar}
Format mix: {bar}

## Replacement briefs (top 5)
For each high-risk ad we propose 1 replacement variation that:
- Lands in a TONE the active mix is under-represented in
- Targets a PERSONA from the brief that isn't covered
- Uses a FORMAT not currently dominating

[per-replacement: hook, primary text, headline, CTA, visual direction, source tier]

## Volume plan (if SHORT)
Current pace: {x} new ads/month
Target: {y} new ads/month
Suggested mix: {easy:medium:hard split} from /jf-bulk-creative

## What NOT to do
- Don't clone the winner with a swapped headline (Andromeda treats them as 1 ad).
- Don't just add more Inspired ads — that's the problem.
- Don't pause ASC ad sets — refresh creative within them.
```

Also output a Google Sheet via `mcp__google-workspace__create_spreadsheet` with all ads + diagnostics + replacement briefs.

### 8. Hand off to /jf-bulk-creative

End with:
```
Recommended next: /jf-bulk-creative --client={client} --count={shortfall} --tones="{under-represented tones}" --funnels="{missing funnels}"
```

## Important Rules

- **Layer 2 is the headline finding.** A clean Layer 1 (no perf decline yet) with broken Layer 2 (90% Inspired) is a ticking bomb — Andromeda compression will hit in 1-2 weeks. Surface this even when current metrics look fine.
- **Never pause ads via this skill.** Per `feedback_no_pause_client_spend.md`. The skill flags, recommends, and briefs the replacements. Humans pause.
- **Naming convention is the input.** If client ads don't follow the JF convention, Layer 2 is impossible. First recommendation in that case: rename + retag via `/jf-deploy-ads` going forward.
- **Win rate 25-35% is normal.** A 30% win rate is not a failure — it's a planning input (`01-creative-production-formula.md`). Don't pathologize losers; plan for them.
- **Volume math is per-client.** Hampton Water at $50/day needs different volume than Grip Studs at $300/day. Always derive from this client's decay+win+budget — never use industry benchmarks.
- **Display all times in user's timezone.**

## Config

`.claude/ops/jf-fatigue-scan/config.json`:

```json
{
  "defaults": {
    "lookback_days": 14,
    "min_lifetime_spend_usd": 100,
    "ctr_decline_threshold": 0.15,
    "frequency_cap": 4.0,
    "hook_rate_floor": 0.25
  },
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "target_cpa_usd": 35,
      "target_winners_simultaneous": 5,
      "historical_avg_winner_lifespan_days": 6,
      "historical_win_rate": 0.30
    }
  }
}
```

## Why this skill exists

External `/fatigue-scan` watches frequency and hook rate. That tells you when an ad is dying, but **not why**, and not what to replace it with. The Jetfuel version diagnoses the root cause (usually emotional monotony, per Edwin's playbook), proposes the right tone/persona/format for each replacement, and hands off to `/jf-bulk-creative` with the gap parameters pre-filled. Anchored in `blog-drafts/05-emotional-creative-fatigue.md` and `01-creative-production-formula.md`.
