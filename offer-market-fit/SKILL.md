---
name: offer-market-fit
description: "Diagnose and fix a brand's offer-market fit using Common Thread Collective's method. Pulls a JF client's live Meta + Shopify data, decides whether a growth plateau is an OFFER problem or a CREATIVE problem, engineers candidate offers, and produces a marketing-moment test plan. Use when the user says 'offer-market fit', 'are we stuck on the offer', 'diagnose the plateau', 'why won't this account scale', 'test new offers for <client>', 'offer testing', or 'offer analysis'. For who/why customer work see persona-researcher; for the creative engine see creative-landscape-scorer."
---

# /offer-market-fit — Offer Testing & Analysis (CTC method)

Runs Common Thread Collective's offer-market-fit sequence against a JF client's live data.
It answers the question 7-figure brands hit: *"We've tried more creative and new ad
structures and we're still stuck. Is the wall an offer problem or a creative problem, and
what offer do we test next?"*

The frameworks, formulas, thresholds, and the fallback AOV↔CVR curve live in
`offer-methodology.md`. Read it before running. Source spine: CTC's
[Offer-Market Fit: Why 7-Figure Brands Hit a Wall](https://commonthreadco.com/blogs/ecommerce-playbook/offer-market-fit-why-7-figure-brands-hit-a-wall)
(Joy Sharma, PE7), enriched with CTC's contribution-margin / MER / new-customer-CAC corpus.

## The one idea

Offer-market fit = a price/value proposition the market will buy at a CAC your unit
economics can fund **in the ad auction**. As spend scales you stop beating mom-and-pop
competitors and start competing against brands with better margins who can afford a higher
CAC. If your offer can't fund that CAC, no amount of creative volume closes the gap. The
sequence is non-negotiable: **product-market fit → offer-market fit → creative strategy.**

## Arguments

- `<client>` — required. Client name or slug; resolved to HQ client_id via config.
- `--benchmark <cac_usd>` — real industry CAC if you have one (Northbeam/client export).
  If omitted, the skill estimates it and tags the result `[ESTIMATE]`.
- `--window <days>` — lookback for the data pull. Default: `last_30d`.
- `--moment "<name>"` — name the cultural moment the test plan should target (e.g.
  "Father's Day", "Back to School"). Optional; otherwise the plan suggests one.

## Workflow

```
1. Resolve client + identity + config
2. Phase 0 — pull unit-economics truth (Shopify AOV/CVR + HQ Meta spend/CAC/CPM/CTR/CPC)
3. Phase 1 — diagnose: OFFER vs CREATIVE vs PRODUCT problem
4. Phase 2 — engineer 3-5 candidate offers (only if Phase 1 verdict = OFFER)
5. Phase 3 — build the marketing-moment test plan + graduation criteria
6. Write the Google Doc + provenance note
```

### 1. Resolve client, identity, config

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/offer-market-fit/config.json` for the client's `hq_client_id`, Shopify
  store handle, known COGS/shipping/fee inputs, and any stored industry benchmark.
- `load_clients_tools` then `list_clients(active_only=true)` → resolve the client_id.

### 2. Phase 0 — unit-economics truth

Pull live data (see `offer-methodology.md` for the formulas):

```
# HQ Meta (spend, new-customer CAC, CPM, CTR, CPC, purchases, conversion_value)
client_performance(client_id, date_start, date_end, platform_filter="meta")
get_platform_insights(platform_id, date_start, date_end, compare_to="previous_period")

# Shopify (AOV, site CVR, order count) — store must be connected; switch-shop if needed
run-analytics-query(...)   # ShopifyQL: net sales, orders, sessions, conversion rate
get-shop-info(...)
```

Compute the **contribution margin per order** (CTC's scoreboard) and reconcile AOV/CVR
across sources. Margin needs real COGS/shipping/fee inputs from config; if missing, prompt
once and tag any margin output `[NEEDS REAL DATA]`.

### 3. Phase 1 — diagnose

Apply the three tests in `offer-methodology.md`:
1. **AOV-to-CAC test** — is industry CAC ≥ AOV? (structural ceiling)
2. **AOV↔CVR curve** — does the brand's (AOV, CVR) sit above or below the curve?
3. **Creative gate** — CTR > 2% and CPC ~ $1 mean creative is adequate.

Output a one-line **verdict**: OFFER / CREATIVE / PRODUCT problem, with the evidence behind
it. If the verdict is CREATIVE, stop here and hand off to `creative-landscape-scorer` /
`jf-fatigue-scan`; if PRODUCT, say so plainly. Only continue to Phase 2 if it's an OFFER
problem.

### 4. Phase 2 — engineer offers

Build 3-5 candidate offers using the CTC perceived-value levers (bundle hero + high-margin,
set-based pricing, free gift, package-only pricing, advertorial LP, friction removal). Each
candidate gets: target AOV, the CVR required to clear the curve at that AOV, the margin
math, and the lever(s) used. See the candidate-offer table template in
`offer-methodology.md`.

### 5. Phase 3 — marketing-moment test plan

Design the de-risked test: unlisted offer, incremental (not cannibalizing), inside a
cultural moment, **statics only**. Define success thresholds (hit rate 2%→7%, AOV×CVR above
curve, affordable CAC) and the graduation criteria to evergreen. Full template in
`offer-methodology.md`.

### 6. Output

Google Doc, default-shared to jetfuel.agency domain as Editor
(`feedback_gdrive_default_editor`):
1. **Verdict** (top line).
2. **Phase 0** scoreboard table.
3. **Phase 1** diagnosis (AOV-to-CAC test + curve placement + creative gate).
4. **Phase 2** candidate-offer table (skip if verdict ≠ OFFER).
5. **Phase 3** marketing-moment test plan + graduation criteria.
6. **Provenance note** — data sources used; every `[ESTIMATE]` and `[NEEDS REAL DATA]`
   called out.

## Iron Rules

1. **Never present a benchmark we didn't get from real data without an `[ESTIMATE]` tag.**
   The industry CAC and the AOV↔CVR curve are estimates unless sourced from real data.
2. **Diagnose before prescribing.** No candidate offers until the OFFER-vs-CREATIVE verdict.
3. **Margin math needs real inputs.** Missing COGS/shipping/fees → tag `[NEEDS REAL DATA]`,
   never invent them (`feedback_no_fabricated_data`).
4. **Respect the sequence.** Don't recommend creative fixes for an offer problem, or offer
   fixes for a product problem.
5. **Never recommend pausing existing client spend** (`feedback_no_pause_client_spend`).
   Frame every test as incremental / in-parallel.

## Red Flags — STOP

- About to write candidate offers when the verdict was CREATIVE → STOP, hand off to the
  creative skills.
- About to state an industry CAC as fact when it came from Meta benchmarks or the heuristic
  curve → STOP, tag it `[ESTIMATE]`.
- About to compute contribution margin with guessed COGS → STOP, prompt for real inputs or
  tag `[NEEDS REAL DATA]`.
- About to recommend a video-heavy test → STOP, CTC tests offers with statics only.
- Used an em dash anywhere → STOP (`feedback_no_emdashes`).

## Voice

Edwin's voice: plain conversational sentences, period-driven (`feedback_proposal_deck_voice`,
`feedback_content_voice`). No em dashes. No fabricated metrics.

## Relationship to other skills

| Question | Skill |
|---|---|
| "Is the wall an offer problem, and what do we test?" | **offer-market-fit** (this one) |
| "Who is the customer / what job are we serving?" | `persona-researcher` |
| "Is the creative engine Andromeda-compliant?" | `creative-landscape-scorer` |
| "Which ads are fatiguing?" | `jf-fatigue-scan` |
| "Deploy the winning offer's ads" | `jf-deploy-ads` |

## Why this skill exists

Most account audits start at the ad account: creative, targeting, structure. CTC's insight
is that a plateaued 7-figure brand is usually hitting a business wall, not a marketing wall.
This skill makes that diagnosis first (offer vs creative vs product), then, only when it's
an offer problem, engineers the offer and a low-risk way to test it. It stops the agency
from burning a creative-refresh budget on a problem creative can't solve.
