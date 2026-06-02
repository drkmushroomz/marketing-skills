---
name: jf-rebalance
description: "Jetfuel budget reallocation — analyzes ROAS across a client's ASC + retargeting + sandbox campaigns, proposes shifts that respect the JF Andromeda 70-80/15-20/5-10 structure, and never auto-pauses client spend. Use when the user says 'rebalance the budget', 'reallocate', 'shift budget', 'where's the budget bleeding', 'optimize spend', 'weekly budget review'."
disable-model-invocation: true
---

# /jf-rebalance — Budget Rebalancer (Jetfuel)

Weekly budget reallocation grounded in the JF 2026 structure (Scale ASC + Manual Retargeting + Sandbox). Compares ROAS across campaigns and ad sets, surfaces shifts, and outputs an executable plan — but **does not auto-execute** by default, because we don't touch client spend without confirmation (`feedback_no_pause_client_spend.md`).

## Architecture aware

The JF account model has three buckets:
- **Scale ASC** (70-80%): Advantage+ Sales, broad — the workhorse, ROAS-optimized
- **Retargeting** (15-20%): Manual remarketing — typically higher ROAS but smaller pool
- **Sandbox** (5-10%): Testing — expected to lose, that's the point

Rebalancing across these is not "shift budget to the highest ROAS bucket." Sandbox should *not* get more budget just because the test winners pulled a 4× day — they need to graduate to Scale first. Retargeting should *not* get more budget than the audience can sustain — frequency caps + audience exhaustion kick in fast.

The Jetfuel rebalance respects this structure.

## Arguments

- Client name. Default: ask.
- `--lookback N` — days of data. Default: 7.
- `--max-shift-pct N` — cap per-bucket adjustment per run. Default: 20% (keep changes small to preserve learning).
- `--min-spend USD` — minimum spend to be in analysis. Default: 100.
- `--target structure|performance` — `structure` rebalances toward the 75/15/10 target; `performance` rebalances toward ROAS within the same buckets. Default: `performance`.
- `--dry-run` — print plan, don't execute. Default: true (always — explicit `--execute` required to push).
- `--execute` — apply via Meta MCP. Requires explicit user confirmation in conversation even if flag is passed.

## Steps

### 1. Load identity, account, goals

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-rebalance/config.json` for client targets, approved budget caps, ASC/Retargeting/Sandbox campaign IDs.
- `get_client(client_id) → client_performance → get_client_goals` → target ROAS, target CPA, monthly budget.
- `get_client_platforms(client_id)` → meta_platform_id, meta_account_id.

### 2. Pull current spend + ROAS per campaign

```
campaigns_performance(
  platform_id={meta_platform_id},
  date_start={now-lookback},
  date_end={now}
)
```

For each campaign: spend, conversions, conversion_value, roas, daily_budget, status.

Categorize each into:
- Scale ASC (match campaign name pattern `JF_Scale_ASC_*`)
- Retargeting (match `JF_Retargeting_*`)
- Sandbox (match `JF_Sandbox_*`)
- **Other** (anything else — legacy campaigns flag for cleanup)

### 3. Pull ad-set-level inside each campaign

```
ad_sets_performance(platform_id={...}, campaign_id={...}, lookback)
```

Per ad set inside Scale ASC: spend, roas, conversions. Inside Retargeting: same plus audience type (visitors / ATC / IC). Inside Sandbox: spend, roas, conversions, **graduation candidacy** (≥X conversions, ROAS > scale ROAS).

### 4. Compute the rebalance plan

Two modes:

**`--target=structure`** — pull buckets toward 75/15/10:
- If Scale ASC < 70% → add budget to ASC, pull proportionally from Retargeting + Sandbox.
- If Sandbox > 10% → cut Sandbox back to 10%, redistribute.
- Apply `--max-shift-pct` cap so changes are gradual (Meta needs stability for learning).

**`--target=performance`** — within each bucket, shift budget toward winners:

*Scale ASC* — typically single ad set, but if multi-ad-set: distribute budget by ROAS, capped at 30% increase per ad set per run.

*Retargeting* — if visitors-30d is at 80% capacity (high frequency) and ATC-14d is at 40%, shift to ATC even if ROAS lower (preserve audience health).

*Sandbox* — never increase a Sandbox campaign's budget. Sandbox winners *graduate* to Scale (separate workflow via `/jf-deploy-ads`). The only Sandbox action: identify graduation candidates and surface them.

### 5. Surface graduation candidates

From Sandbox, any ad set/ad meeting all of:
- ≥ 7 days of data
- ≥ 20 conversions
- ROAS ≥ Scale ASC ROAS × 0.85
- Frequency < 3.0
- Naming convention matches a tone/format under-represented in Scale

→ flag as **GRADUATE TO SCALE** with a `/jf-deploy-ads --target=scale --variation-ids=...` command pre-written.

### 6. Build the plan report

```
# /jf-rebalance — {Client} — {date}

## Current allocation
| Bucket | Daily Budget | % of total | 7d ROAS | 7d CPA | Verdict |

## Recommended allocation
| Bucket | New Budget | Δ | Reason |

## Ad set shifts within buckets
[per-bucket tables]

## Graduation candidates (Sandbox → Scale)
| Ad set | Ad | Conv | ROAS | Suggested action |

## Cleanup flags
- {N} legacy campaigns outside the JF structure spending ${X}/d — review

## Projected weekly impact
Best case: ${X} additional revenue
Worst case (no improvement): no change in spend
Assumption: ROAS holds at current rates
```

### 7. Execute (only if explicitly confirmed)

If `--execute` AND the user confirms in-conversation:
- Call `mcp__meta__*` ad set update endpoint for each change. (Use the campaign budget update if budgets live at campaign level under CBO.)
- 0.5s between calls. Retry once on 429.
- Skip any change that exceeds the approved client budget cap from config.
- **Never pause anything.** If a recommended change would require pausing (e.g. "this losing ad set should go to $0"), surface it as "Recommend strategist pause: {ad set}" — do not zero its budget yourself.

If `--dry-run` or no confirmation: write the plan and exit.

### 8. Write to HQ + Slack

Append the change list to HQ `client_changes(client_id=...)` so the audit trail records what shifted and why. Post a brief summary to the client's Slack channel (from `jf-bleed-check` config) — the strategist and the client can both see what moved.

## Important Rules

- **Default is dry-run. `--execute` requires in-conversation confirmation.** Even with flag passed, prompt: "About to shift ${X} across {N} ad sets — confirm?"
- **Never pause ads or ad sets.** Move budget down to a config minimum, but never to $0. Pausing is a human decision (`feedback_no_pause_client_spend.md`).
- **Respect approved budget cap.** Any aggregate increase that pushes daily spend over the cap in config is refused.
- **Sandbox budgets only DECREASE via this skill.** Increases happen via graduation, not rebalance.
- **Max-shift-pct keeps Meta learning stable.** Don't shift more than 20% of an ad set's budget in a single run — bigger shifts kick the learning phase.
- **Naming convention or it didn't happen.** If campaigns don't match `JF_Scale_ASC_*` / `JF_Retargeting_*` / `JF_Sandbox_*`, refuse to rebalance and surface the "Other" bucket for cleanup first.
- **HQ writeback is best-effort.** If `client_changes` fails, log to local audit, don't abort the Meta calls.
- **Display all times in user's timezone.**

## Config

`.claude/ops/jf-rebalance/config.json`:

```json
{
  "defaults": {
    "max_shift_pct": 20,
    "min_per_adset_daily_usd": 5,
    "target_split": {"scale": 75, "retargeting": 15, "sandbox": 10}
  },
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "approved_total_daily_budget_cap_usd": 800,
      "target_roas": 2.5,
      "campaigns": {
        "scale_pattern": "JF_Scale_ASC_HamptonWater",
        "retargeting_pattern": "JF_Retargeting_*HamptonWater*",
        "sandbox_pattern": "JF_Sandbox_HamptonWater"
      }
    }
  }
}
```

## Why this skill exists

External `/rebalance` treats all ad sets equally and shifts to top ROAS. That breaks the JF Andromeda structure: it'd over-fund Sandbox the moment a test pulls a winning day, or starve Scale because Retargeting always wins on ROAS. The Jetfuel version respects the three-bucket model, treats Sandbox as an investment in graduation candidates (not a perf bucket), and never auto-pauses.
