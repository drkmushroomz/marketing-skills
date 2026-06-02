---
name: creative-landscape-scorer
description: Use when scoring a brand's Meta creative landscape against the Andromeda 2026 algorithm rules — symptoms include "Andromeda audit", "Andromeda readiness", "score their ads", "creative landscape audit", "are they running Andromeda-compliant creative", "Entity ID diversity check", "creative fatigue audit", "are they fragmenting budget", "is their refresh cadence healthy", "Meta CAPI audit", or any audit where the question is "is the creative engine set up correctly for the algorithm" rather than "who are they targeting" (for that, see persona-researcher).
---

# Creative Landscape Scorer

## Overview

Scores a brand's Meta creative landscape against the Andromeda 2026 algorithm rules using a 6-dimension rubric. Outputs a weighted composite score (0–10) + per-dimension diagnostic + ranked next-step moves. The deliverable goes into a Google Doc that drops into an audit / proposal / QBR deck.

This skill is about **algorithm fit** — is the creative engine structured the way the Meta algorithm rewards. It does NOT do persona / JTBD / customer research (use `persona-researcher` for that). The two skills are complements: persona-researcher answers "who are we talking to and what jobs do they have", creative-landscape-scorer answers "is the creative machinery set up correctly to scale on Meta in 2026."

When both are warranted (full audit, new prospect, QBR), run persona-researcher first to ground the personas, then creative-landscape-scorer to score the engine and surface Andromeda-violating anti-patterns.

Two modes:
- **Prospect mode** — HQ Recon scrape only. Used for new business and audits.
- **Client mode** — Adds HQ creative-fatigue / scoring on the client's own ads. Used for QBRs and ongoing strategy.

Voice for the output doc: match `feedback_proposal_deck_voice` (plain conversational, period-driven). Never fabricate metrics — see `feedback_no_fabricated_data`. Never recommend pausing existing spend — see `feedback_no_pause_client_spend`.

## When to Use

| Trigger | Skill |
|---|---|
| "Score their Meta creative" / "Andromeda audit" / "is their setup algorithm-fit" | **creative-landscape-scorer** (this one) |
| "Build the personas" / "JTBD analysis" / "who are they targeting" | `persona-researcher` |
| Full prospect audit / new-client onboarding deck | Run both. Persona first, then scoring. |
| Client QBR — "why isn't ROAS scaling" | Both, plus HQ `creative_tag_analytics` for client-side fatigue. |

**Don't use** for one-off ad reviews (`top_creatives` is enough), for swipe-file curation (use `recon_*` HQ tools directly), or for site-only CRO audits (no creative-engine component).

## Workflow

```
1. Identify the brand + mode (prospect or client)
2. Pull ad data from HQ Recon (see "Ad data source" below)
3. If client mode: also pull HQ creative_summary, top_creatives, creative_tag_analytics
4. Score the landscape against the 6-dim Andromeda rubric (see scoring-rubric.md)
5. Cross-reference observed themes vs the course taxonomies (10 Creative Formats,
   10 UGC Strategies, 16 Human Desires) to identify gaps
6. Synthesize: ranked next steps with effort/impact tags
7. Output to Google Doc (or append as Appendix to existing audit)
```

If the audit also needs persona work (most prospect decks do), run `persona-researcher` first and reference its output here.

## Quick Reference

### The Andromeda 6-Dim Scoring Rubric

| Dimension | What we measure | Source |
|---|---|---|
| 1. Entity ID Diversity | How many visually distinct concepts (not aspect-ratio variations) cover ≥2 of: Format / Persona / Environment / Benefit. Target: 10–15 Entity IDs across 3+ personas | Recon `list_recon_ads` — group by visual concept |
| 2. Targeting Breadth | All 5 placements active? CTA variety? Lookalike-style fragmentation? | Recon scrape (placements + CTA distribution) |
| 3. Budget Adequacy | Are they fragmenting <$50–100/Entity ID? (only fully scorable in client mode) | HQ `creative_summary` + ad count |
| 4. Refresh Cadence | % of active ads launched in last 30 / 60 / 90 days. Healthy: 30%+ in last 30d | Recon `started_running_at` field |
| 5. Data Signal | Meta Pixel firing? CAPI on? GA4 + Google Ads tags present? | View-source of homepage + 1 PDP |
| 6. Vertical Coverage | Format mix vs top 3 vertical competitors (the course's 10 Creative Formats) | Add competitors to Recon, run same scoring |

Full rubric + scoring formulas + anti-pattern catalog: see `scoring-rubric.md` in this directory.

### Ad data source (in priority order)

1. **PREFERRED: HQ Recon** (`mcp__jetfuel-hq__list_recon_*`). Already scrapes the Meta Ad Library on Jetfuel's infrastructure, normalizes ads, ranks hooks by `days_running` (= market-validation proxy), maintains a shared CreativeTag taxonomy. Workflow:
   - `search_recon_brand_candidates` → find the right Meta page_id
   - If `already_tracked: true` → skip ahead to analytics
   - Else `preview_add_recon_brand` + `add_recon_brand` → dispatches scrape, ~5 sec wait
   - `get_recon_brand_analytics` → media mix + top 5 longest-running hooks
   - `list_recon_hooks` → hooks ranked by days_running
   - `list_recon_ads(sort=longest_running)` → primary_text, headline, CTA, link_url, started_running_at
2. `mcp__meta__meta_ad_library_search` (requires Meta App Review unlock — see `reference_meta_ad_library_api`)
3. **Last resort:** `python scripts/scrape_ad_library.py "<Brand>"` Playwright fallback. Only use if Recon is genuinely unavailable.

### HQ tools (Client mode only)

| Tool | What it gives you |
|---|---|
| `mcp__jetfuel-hq__creative_summary` | Top-line creative KPIs with period-over-period |
| `mcp__jetfuel-hq__top_creatives` | Top N performing ads with AI tags |
| `mcp__jetfuel-hq__creative_tag_analytics` | Performance by tag (hook_tactic, creative_format, intent) — finds fatigued formats |
| `mcp__jetfuel-hq__list_creative_ads` | All ads with per-ad metrics for full-account scoring |
| `mcp__jetfuel-hq__compare_creative_periods` | Period-over-period delta narrative |
| `mcp__jetfuel-hq__client_changes` | Humanized changelog — context for why metrics moved |

## Course Taxonomy Anchors (for gap identification)

Reference the internal course (Drive folder `18mtNwn_IZ-er4e31r3AKeA2XgAy-Ja_B`):

- **10 Creative Formats** (Module 03)
- **10 UGC Strategies That Convert** (Module 03)
- **15 Creatives for Service / B2B / Info Products** (Module 03)
- **16 Human Desires** (Module 04)
- **Advertising Strategies That Scale (Big Swings)** (Module 04)
- **Copywriting That Converts — Primary Text** (Module 04)
- **Creative Analytics Cheatsheet** (Module 09, doc `1SaBQPrZbivYSsmrMDOjknwYX-kBr6GCn9Sb7JpDWDlM`)

## Output Template

1. **Top-line scorecard** — 6 dimensions × 0–10 × one-line read
2. **What's working** — Andromeda-aligned signals (quote specific evidence)
3. **What's leaking** — Andromeda violations with the specific anti-pattern named
4. **Content gaps in the vertical** — which of the 10 Formats / 10 UGC Strategies / 16 Desires are missing
5. **Ranked next steps** — top 5, each tagged Effort (S/M/L) and Impact (S/M/L)
6. **What we'd want to verify with access** (prospect mode) OR **Client-data caveats** (client mode)

## Common Mistakes

| Mistake | Fix |
|---|---|
| Confusing Meta Ad Library "result count" with the brand's actual active ad count | Use Recon counts, which are normalized. The Library keyword-search count includes false positives. |
| Counting aspect-ratio variations as Entity IDs | Per Andromeda: 1:1 + 4:5 + 9:16 of the same creative = 1 Entity ID |
| Recommending a pause to existing spend | Forbidden by `feedback_no_pause_client_spend`. Frame as "in parallel." |
| Fabricating ROAS / CPA when scope is prospect-mode | Use `[NEEDS REAL DATA]` placeholders. Hard rule per `feedback_no_fabricated_data` |
| Recommending lookalikes | Per `feedback_meta_ads_2026`: no lookalikes in 2026. Use creative-as-targeting. |
| Scoring Data Signal as "fine" because Pixel is in page | Pixel ≠ CAPI. Check `facebookCapiEnabled` in the page-config blob. |
| Running this skill without persona context | Personas drive what "good" creative looks like. For any prospect proposal, run `persona-researcher` first. |

## Red Flags — STOP

- About to recommend "pause everything" → STOP, frame as in-parallel
- About to invent a ROAS number → STOP, mark `[NEEDS REAL DATA]`
- About to score Entity ID Diversity as high because there are "lots of ads" → STOP, group by visual concept first
- About to add lookalike audiences to Next Steps → STOP, it's creative-as-targeting in 2026
- About to recommend creative changes without persona context → STOP, run `persona-researcher` first
