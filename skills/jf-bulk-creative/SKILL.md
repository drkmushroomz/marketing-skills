---
name: jf-bulk-creative
description: "Jetfuel creative factory — scale a single winning angle into 30-100 ad variations using the JF easy/medium/hard sourcing tiers, 4-tone emotional matrix, 12-theme taxonomy, and the [Brand]_[Tone]_[Persona]_[Funnel]_[Format]_[Version] naming convention. Use when the user says 'bulk creative', 'spin up variations', 'creative factory', '50 ads from this winner', 'graduate this hook', 'scale creative', or has a winning ad and needs the next round."
disable-model-invocation: true
---

# /jf-bulk-creative — Creative Factory (Jetfuel)

Take a winning ad (or a single brief) and produce a production-ready variation set that respects the JF Andromeda playbook. Outputs creative briefs, copy variations, asset specs, and the manifest the production team feeds into `/jf-deploy-ads`.

Built around `blog-drafts/06-ten-to-hundred-ads.md` and `01-creative-production-formula.md`.

## What this skill does NOT do

It does **not** mass-render PNGs via Puppeteer like the generic `/bulk-creative`. Jetfuel's creative is filmed/shot/sourced through the factory model (UGC ~$83, AI ~$0.17, in-house ~$6000). The output is a brief set + variation manifest the producers execute, not auto-rendered ads.

If you want pure AI-rendered statics for a sandbox test, append `--ai-render` and we'll route through the Statamic/Cloudflare image pipeline.

## Arguments

- Client name. Default: ask.
- `--seed-ad ad_id` — the winning ad to graduate from. Reads from HQ via `get_creative_ad`.
- `--seed-angle "..."` — alternative if no seed ad: paste the winning hook/angle.
- `--count N` — total variations. Default: pull from `/jf-fatigue-scan` recommended monthly volume, or use 30 if unspecified.
- `--mix easy:medium:hard` — production mix. Default: `50:25:25` per the JF playbook.
- `--tones "Assured,Worried,Inspired,Amused"` — comma list, default all 4 with no single tone >50%.
- `--personas "..."` — comma list from the client brief.
- `--funnels "TOFU,MOFU,BOFU"` — comma list, default all 3.
- `--formats "UGC,founder-led,vertical-static,carousel,Reels"` — Andromeda-priority formats default-on.

## Steps

### 1. Load identity, brief, fatigue context

- Read `.claude/me.md`.
- Read `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md` (brand voice, personas, approved claims, founder availability, asset library).
- Read the most recent `.claude/ops/jf-fatigue-scan/reports/{client-slug}-*.md` for current monthly volume target.
- Read `.claude/ops/jf-bulk-creative/config.json` for client-specific cost overrides.
- Read `.claude/edwin-tone-guide.md` for voice anchoring.

### 2. Resolve the seed

If `--seed-ad`:
```
hq.get_creative_ad(ad_id={seed_ad})
hq.get_campaign_detail(campaign_id={ad.campaign_id}, platform_type="meta")
```
Extract: hook, primary text, headline, CTA, format, persona inferred from naming convention, current performance (spend, CTR, ROAS, hook-rate).

If `--seed-angle`: parse the angle into its emotional core (which of the 4 tones?), problem/pain identified, the implicit persona, the underlying claim.

### 3. Compute the variation plan

The JF rule: **variation = structural difference, not surface edit**. Per `02-andromeda-algorithm.md`, swapping a headline word does nothing — Andromeda still treats them as 1 ad. So the variation axes are:

| Axis | Levels | Andromeda effect |
|---|---|---|
| Emotional tone | Assured / Worried / Inspired / Amused | HIGH — different auction entry |
| Persona target | from client brief | HIGH |
| Funnel stage | TOFU / MOFU / BOFU | HIGH |
| Hook category | curiosity / pain / proof / outcome / story | MEDIUM-HIGH |
| Format | UGC / founder / vertical static / carousel / Reels | HIGH |
| Source tier | easy / medium / hard | (production cost) |

Build the matrix: target `--count` variations spread across axes such that NO single combination dominates. Apply Edwin's rule: no single tone >50%, ≥3 of 4 tones present.

### 4. Generate per-variation brief

For each of the `--count` rows, produce a brief with:

- **ID**: `{Client}_{Tone}_{Persona}_{Funnel}_{Format}_v{NN}` (the JF canonical naming convention from `blog-drafts/05-emotional-creative-fatigue.md`)
- **Source tier**: easy / medium / hard (mapped from mix ratio)
- **Hook** (≤8 words, structurally different from seed)
- **Primary text** (≤125 chars, Edwin voice — see `edwin-tone-guide.md`)
- **Headline** (≤40 chars)
- **CTA** (Shop Now / Learn More / Try Free etc — choose based on funnel stage)
- **Visual direction** (one sentence — what the camera sees in second 1, e.g. "founder holds product, kitchen background, mid-morning light")
- **Asset cost estimate** (per source tier table below)
- **Producer notes** (talent type, location, length, must-include shots)

Source-tier production rules:

| Tier | What it is | Cost/unit | Producer |
|---|---|---|---|
| **Easy** (~50%) | Repurpose existing — chop long-form, remix organic | ~$0.17 (AI assist) | In-house editor + AI |
| **Medium** (~25%) | Founder/team phone clips, in-warehouse, on-shelf comparisons | ~$0 (internal time) | Client team |
| **Hard** (~25%) | UGC sourcing, paid creators, influencer footage rights | ~$83 (UGC marketplace) | UGC vendor |

### 5. Apply the JF brand-voice filter

Pass every primary text / headline through:
- `.claude/edwin-tone-guide.md` (anti-AI-tells checklist, no "Here's the thing", no "Let that sink in")
- Client brief approved-claims list — anything making medical/health claims that isn't approved gets flagged
- The 4 tones — confirm each variation lands cleanly in one (not muddled)

### 6. Apply Andromeda compression check

Take the full set, group by **core message** (strip visual differences, ask: what claim does this ad make?). If more than 25% cluster in one message, reject and regenerate — that's the same trap as the variant strategy that died in 2020.

### 7. Build the variation manifest

Write `.claude/ops/jf-bulk-creative/manifests/{client-slug}-{YYYY-MM-DD}.json` with shape:

```json
{
  "client": "hampton-water",
  "seed_ad_id": 12345,
  "generated_at": "2026-05-19T...",
  "playbook_version": "andromeda-v14",
  "summary": {
    "total": 50,
    "by_tone": {"Assured": 14, "Worried": 12, "Inspired": 13, "Amused": 11},
    "by_funnel": {"TOFU": 18, "MOFU": 17, "BOFU": 15},
    "by_source_tier": {"easy": 25, "medium": 13, "hard": 12},
    "estimated_total_cost": "$1,124"
  },
  "variations": [
    {
      "id": "HamptonWater_Inspired_FrequentTraveler_TOFU_UGC_v01",
      "tier": "hard",
      "format": "UGC vertical 9:16",
      "hook": "...",
      "primary_text": "...",
      "headline": "...",
      "cta": "Shop Now",
      "visual_direction": "...",
      "producer_notes": "...",
      "estimated_cost_usd": 83
    }
  ]
}
```

### 8. Build the producer-facing brief sheet

Output a Google Sheet via `mcp__google-workspace__create_spreadsheet`:

| Tab | Contents |
|---|---|
| Briefs (per-variation) | One row per variation: full brief + cost + due date |
| Production plan | Pivot: tier × producer × delivery week |
| Naming guide | The naming convention, with examples |
| Andromeda check | Theme/tone/format distribution chart, compression-risk score |

### 9. Optional: stage in the Shelf + Warehouse model

If `--stage-paused`, hand the manifest to `/jf-deploy-ads --mode=draft` so all variations get built as PAUSED ads in the Meta account, ready for activation when sandbox/scale campaigns need refreshing. Per `blog-drafts/06-ten-to-hundred-ads.md`: "build all 70 pieces of ad copy and landing page combinations, leave them paused in the account, and activate them as needed."

### 10. Present in-conversation summary

```
{N} variations generated for {client}, mixed {easy}/{medium}/{hard} across {tones} tones.
Compression check: PASS. Andromeda diversity score: {x}/14.
Producer brief sheet: {link}. Manifest: {path}.
Estimated total cost: ${X}.
```

Then: "Want me to /jf-deploy-ads in draft mode so the team can activate from the warehouse?"

## Important Rules

- **Structural variation, not surface variation.** Different hook word ≠ different ad. Different tone + persona + funnel = different ad. (`blog-drafts/02-andromeda-algorithm.md`)
- **Respect client founder availability.** If the client brief says "founder is camera-shy" or "no founder access until Q4," reduce founder-led count and rebalance.
- **Never fabricate UGC or invent talent.** Producer notes describe the brief, not the deliverable.
- **No claim escalation.** A variation that promises something stronger than the seed (a bigger result, a faster time, a clinical claim) gets flagged unless the brief says it's approved.
- **No emdash mid-sentence punch lines.** See `feedback_content_voice.md` — AI tells. Edwin doesn't write that way.
- **Apply the cost-aware split.** Don't propose 50 UGC variations at $83 each ($4,150) when the client's monthly creative budget is $1,500. Surface the dollar cost on every plan.
- **The Sheet is the deliverable.** Conversation print is a preview.

## Config

`.claude/ops/jf-bulk-creative/config.json`:

```json
{
  "default_mix": "50:25:25",
  "cost_overrides_usd": {
    "easy": 0.17,
    "medium": 0,
    "hard": 83,
    "inhouse_polished": 6000
  },
  "clients": {
    "hampton-water": {
      "founder_available": true,
      "founder_name": "Jesse Bongiovi",
      "ugc_vendor": "Insense",
      "monthly_creative_budget_usd": 3500
    }
  }
}
```

## Why this skill exists

External `/bulk-creative` skills auto-render PNGs in Puppeteer. That worked when Meta rewarded volume of look-alike variants. **Andromeda killed that workflow** (`blog-drafts/02-andromeda-algorithm.md`). The Jetfuel version produces *production briefs* across structural axes — what the team actually executes — and prices the plan in dollars so the strategist doesn't ship a $5K plan to a $1K client.
