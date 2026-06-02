---
name: persona-researcher
description: Use when building or auditing customer personas for a D2C / Meta-ad brand — symptoms include "research the personas", "who are they targeting", "find the persona gaps", "build personas from their ads", "JTBD analysis", "jobs to be done", "Schwartz awareness stages", "audience research", "VOC analysis", "customer-research", "who is the customer", "what jobs are we serving". For scoring the creative engine against Andromeda algorithm rules, see creative-landscape-scorer instead.
---

# Persona Researcher

## Overview

Builds evidence-based customer personas for D2C / Meta-ad brands. Derives personas from JTBD job-clusters supported by 3+ market-validated hooks (ranked by `days_running` in HQ Recon), maps every hook to a Schwartz awareness stage, runs claude-persona AI panel validation, and cross-references against competitors.

This skill is about **who** and **why**. For **how is the creative engine structured** (Andromeda algorithm fit, Entity ID diversity, refresh cadence, CAPI status), use `creative-landscape-scorer`. The two skills are complements and often run together on full audits — persona-researcher first to ground the personas, then creative-landscape-scorer to score the engine.

The methodology is in `persona-methodology.md`. It encodes four public frameworks: Eugene Schwartz's 5 Levels of Awareness, Jobs-to-be-Done (Bob Moesta / Tony Ulwick), Corey Haines's customer-research framework, and the takechanman1228/claude-persona AI-panel pattern.

Two modes:
- **Prospect mode** — HQ Recon scrape of the prospect + their top competitors.
- **Client mode** — Adds VOC sources (transcripts, support tickets, reviews) via the Corey Haines extraction framework + HQ `creative_tag_analytics` for AI-tagged persona-per-ad data.

Voice for the output doc: match `feedback_proposal_deck_voice` (plain conversational, period-driven). No fabricated metrics — see `feedback_no_fabricated_data`. No averaged personas, no single-source personas — see `persona-methodology.md` Iron Rules.

## When to Use

| Trigger | Skill |
|---|---|
| "Build the personas" / "Who is the customer" / "JTBD analysis" | **persona-researcher** (this one) |
| "Score their Meta creative engine" / "Andromeda audit" | `creative-landscape-scorer` |
| Full prospect audit / new-client onboarding deck | Run both. Persona first, then landscape scoring. |
| Client QBR — "why isn't ROAS scaling, are we talking to the right people" | Persona-researcher (lens) + creative-landscape-scorer (engine). |
| Ad creative brief / hook ideation | Persona-researcher (the hook style follows from the persona's awareness stage). |

**Don't use** for ad-level performance review (`top_creatives`), swipe-file curation (`recon_*`), or pure ad-tech audits without a customer angle (`creative-landscape-scorer`).

## Workflow

```
1. Identify the brand + mode (prospect or client)
2. Pull ad data from HQ Recon — preferred path (see "Ad data source" below)
3. If client mode: pull VOC sources (transcripts/reviews/tickets via google-workspace + slack)
   and HQ creative_tag_analytics with category_slug=persona|intent
4. Run the persona methodology (see persona-methodology.md):
   - Extract JTBD (functional/emotional/social) from each market-validated hook
   - Map each hook to a Schwartz awareness stage
   - Cluster hooks → derive personas (3+ supporting hooks per cluster)
   - Apply confidence labels (High / Medium / Low)
   - Dispatch claude-persona AI panel for validation
5. Pull competitor data — add competitors to Recon if not tracked — and build the
   competitor × persona cross-reference matrix
6. Identify persona gaps (where competitors play but the brand doesn't)
7. Output to Google Doc with: summary table, per-persona deep-dives, competitor
   matrix, ranked next-step persona moves
```

## Quick Reference

### Ad data source (in priority order)

1. **PREFERRED: HQ Recon** (`mcp__jetfuel-hq__list_recon_*`). Hooks come ranked by `days_running` — the market-validation signal that drives persona derivation in this methodology.
   - `search_recon_brand_candidates` → find Meta page_id
   - `preview_add_recon_brand` + `add_recon_brand` if not tracked (~5 sec scrape)
   - `get_recon_brand_analytics` → media mix + top 5 longest-running hooks
   - `list_recon_hooks(limit=25)` → all hooks ranked by days_running
   - `list_recon_ads(sort=longest_running)` → primary_text, headline, link_url, started_running_at per ad
2. `mcp__meta__meta_ad_library_search` (requires Meta App Review unlock)
3. Last resort: `python scripts/scrape_ad_library.py "<Brand>"` Playwright fallback

### Public frameworks (encoded in persona-methodology.md)

- **Eugene Schwartz — 5 Levels of Awareness** (Unaware → Problem-Aware → Solution-Aware → Product-Aware → Most-Aware). Every hook maps to one stage. ([Motion App's DTC adaptation](https://motionapp.com/blog/five-customer-awareness-stages-advertising))
- **Jobs-to-be-Done** — functional + emotional + social jobs as the persona-derivation source. Personas derive from jobs, not vice versa. ([Strategyn](https://strategyn.com/jobs-to-be-done/))
- **Corey Haines's customer-research skill** — JTBD-functional/emotional/social, confidence labels, frequency × intensity ranking, persona template structure. ([coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills/blob/main/skills/customer-research/SKILL.md))
- **takechanman1228/claude-persona** — AI persona panel pattern for hypothesis validation. ([github](https://github.com/takechanman1228/claude-persona))

### Iron Rules (from persona-methodology.md)

1. No persona without **3+ market-validated hooks** pointing to the same job-cluster.
2. Don't average across distinct personas — separate buckets even if demographics overlap.
3. Capture **exact ad copy verbatim** — verbatim hooks become persona vocabulary.
4. Label every persona with **confidence: High / Medium / Low**.
5. Don't invent demographics — leave blank or label as inference.
6. Cross-reference, don't echo — if a "persona" is just brand positioning copy, it's not a persona.

### HQ tools that augment client-mode persona work

| Tool | What it gives you |
|---|---|
| `mcp__jetfuel-hq__creative_tag_analytics` (category_slug=persona\|intent) | AI-tagged persona-per-ad data — the closest thing to a "true" persona attribution we have |
| `mcp__jetfuel-hq__top_creatives` | Highest-ROAS ads (overrides longevity as the validation signal in client mode) |
| `mcp__jetfuel-hq__get_context_events` (types=[client_request, creative_decision, client_sentiment]) | Declared target-customer context from meeting recaps |
| `mcp__claude_ai_Google_Drive__search_files` + `read_file_content` | VOC sources (interview transcripts, surveys, customer notes) |
| `mcp__slack__conversations_search_messages` | Customer feedback shared in Slack |

## Output Template (Persona Section)

The persona analysis goes into a Google Doc with these sections:

1. **Methodology note** — sources used, framework references, iron-rule compliance statement
2. **Raw evidence table** — every market-validated hook with days_running, Schwartz stage, implied job
3. **Derived personas** — per-persona deep-dive (job, trigger, pain, vocabulary, evidence, confidence)
4. **Personas the brand is NOT addressing** — gap personas with their own evidence pattern
5. **Competitor × persona cross-reference matrix**
6. **Ranked persona-driven next moves** — top 5, tagged Effort/Impact

If this skill is run as part of a broader audit, the persona section becomes an Appendix to the audit doc.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Eyeballing personas from ad creative thumbnails | Use `persona-methodology.md`. Personas require 3+ market-validated hooks per cluster |
| Naming personas from creative tone alone ("the foodie") | Persona = job-cluster, not creative vibe |
| Counting persona presence with check marks | Count by # of supporting hooks, not yes/no |
| Single-source persona | Iron Rule #1 — need 3+ hooks |
| Persona that's just the brand's positioning statement | That's marketing copy, not a customer |
| Recommending lookalike audiences off persona work | Per `feedback_meta_ads_2026` — creative-as-targeting in 2026 |
| Skipping competitor recon | Personas without competitive context = strategy without map |
| Running persona work without recon ad data | Persona claims require evidence. Pull `list_recon_hooks` first. |

## Red Flags — STOP

- About to assign a persona to an ad based on the thumbnail only → STOP, group by job-cluster across multiple hooks
- About to use any persona with 1–2 supporting hooks at confidence High → STOP, downgrade to Medium
- About to recommend lookalike-audience targeting based on persona insights → STOP, use creative-as-targeting
- About to skip the competitor matrix → STOP, the gaps live in the matrix
- About to ship the persona section without the claude-persona AI panel validation step → STOP, dispatch the panel
