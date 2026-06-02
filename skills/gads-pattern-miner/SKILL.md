---
name: gads-pattern-miner
description: Mine Google Ads test history (RSA assets, search terms, keywords, ad performance) for a single client account, identify statistically meaningful winners/losers, and append findings to a per-client living knowledge base. Use when the user wants to "mine patterns from <client>'s Google Ads", "update the gads notebook for <client>", "run continuous learning on <client>", or asks what's actually working in an ad account. Optimized for weekly cadence — only fetches data since last run.
---

# Google Ads Pattern Miner

Mines a client's Google Ads account for statistically significant patterns and appends them to a per-client markdown knowledge base. Token-budgeted for ~50K first run, ~20K weekly delta.

## When to invoke

- "Mine patterns from <client>'s ads"
- "Update the gads pattern notebook"
- "What's working in <client>'s Google Ads?"
- Weekly cron for continuous learning

## Prerequisites

- `scripts/gads_tokens.json` exists (run `scripts/gads_auth.py` once if not)
- Client's Google Ads CID known — find via HQ `get_client_platforms`
- For L90D first run on a new client, the per-client `<slug>.md` does not yet exist

## **REQUIRED preflight — set the KPI lens**

Before running, pull the client's goal structure so the analysis isn't framed against the wrong KPI:

1. `mcp__jetfuel-hq__list_clients` → client_id
2. `mcp__jetfuel-hq__get_client_goals` → read sub-goal names (e.g. "Store Visits", "Engagement", "Reach", "Pear Conversion", "Branded")
3. Skim Slack `#<client>` / `#jf-<client>` and Gmail (newer_than:30d) for active KPI language
4. Classify the account:

| KPI lens | Signals in goals/comms | What "winner" means | What `--kpi-type` to pass |
|---|---|---|---|
| **TOF / brand** | YouTube In-Stream + Shorts budgets, "engagement", "reach", "view rate", "CPM", Tracksuit | Cheap CPM, high view rate, branded-search lift over time | `tof` |
| **Retail / omnichannel** | PMAX Store Locator, Pear Commerce, Walmart/Target proximity, "store visits" | Store-visit cost, retail sell-through, branded lift in DMA | `retail` |
| **DTC / performance** | "Conversion", "ROAS", "CAC", "purchase", e-com only | Blended CAC, ROAS, MER | `dtc` (default) |
| **Lead-gen** | "leads", "CPL", "MQL", form-fill goals | CPL, MQL→SQL, downstream pipeline | `lead-gen` |

**Don't apply a CPA/ROAS lens to a TOF or Retail account.** Video spend with $0 online conv is *not a leak* if the goal is brand reach. Store-visit conversions from PMAX Local are *the metric*, not "fake CPA."

## Run

```bash
python .claude/skills/gads-pattern-miner/mine.py \
  --client <slug> --cid <customer_id> --days 90 \
  --kpi-type <tof|retail|dtc|lead-gen>
```

For TOF/retail accounts, the script additionally pulls:
- Video metrics by campaign (CPM, CPV, view rate, quartile completion)
- Branded-term monthly trend (TOF lift proxy)
- Conversion category breakdown (STORE_VISIT vs PURCHASE etc.)

Outputs:
- `.claude/skills/gads-pattern-miner/data/<slug>_raw.json` (full pulled data, not for context)
- Stdout: pre-aggregated top-N tables (this is what Claude reads)
- Claude then appends structured findings to `knowledge-base/<slug>.md`

## Token discipline

**DO:**
- Read only the script's stdout summaries
- Read the existing `<slug>.md` if it exists (for delta-only mining)
- Write findings in the structured format below

**DON'T:**
- Read `<slug>_raw.json` unless investigating a specific anomaly
- Dump campaign-by-campaign tables into the response
- Re-mine patterns already in `<slug>.md` (check `_meta.json` for last-run date)

## Knowledge base format

Each `knowledge-base/<slug>.md` follows:

```markdown
# <Client> — Google Ads Pattern Notebook
_Last mined: YYYY-MM-DD (L<N>D)_
_Account: <CID>_

## Confirmed winners
- **<Pattern>** — <lift metric> (n=<sample>, p<<0.05>) [<date observed>]

## Confirmed losers
- **<Pattern>** — <drop metric> [<date observed>]

## Open questions
- <Pattern>: trending but sample size too small (n=<N>)

## Test inventory
- Active experiments: <count>
- Last A/B observed: <date>
- Untested hypotheses worth running: <list>
```

After 3+ clients show the same pattern, promote to `_global.md`.

## Mining checklist

1. Read existing `<slug>.md` and `_meta.json` (skip if first run)
2. Run `mine.py` with appropriate `--days`
3. Review stdout summaries — only look at JSON for outliers
4. For each candidate pattern: check sample size, compute lift, assign confidence
5. Append new findings; mark superseded findings as `[updated <date>]`
6. Update `_meta.json` with run timestamp and account CID

## Statistical thresholds

- **Confirmed winner/loser:** n ≥ 1000 imp, lift ≥ 20%, p < 0.05 (chi-square on CTR; t-test on CVR)
- **Open question:** n < 1000 or 0.05 ≤ p < 0.15
- **Skip:** n < 100 or directionally noisy

## KPI lens declarations (top of every `<slug>.md`)

The first section of every per-client KB file must declare the account's KPI lens so future mining runs don't drift back to default DTC framing:

```markdown
## Account framing
- **KPI lens:** TOF / brand awareness (or: retail / dtc / lead-gen)
- **Primary metrics:** CPM, video view rate, branded-search monthly lift, store visits
- **What 'leak' means here:** broad-match category waste in the small Search Prospecting budget. NOT video spend with $0 online conv (that's intentional).
- **Source:** HQ get_client_goals + Slack #<client>
```
