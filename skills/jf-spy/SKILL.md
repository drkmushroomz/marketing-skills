---
name: jf-spy
description: "Jetfuel competitor ad intelligence scan. Pulls active Meta ads from a client's competitor set, diffs against last week's pull, classifies every new ad against the JF 12-theme / 4-tone / Andromeda taxonomy, and surfaces the angles your client is missing. Use when the user says 'spy on competitors', 'what are competitors running', 'creative recon', 'check the ad library', 'what's new in {brand}'s ads', or wants a weekly competitive pulse for a JF client."
disable-model-invocation: true
---

# /jf-spy — Competitor Ad Recon (Jetfuel)

Weekly competitor ad recon, grounded in the JF Andromeda playbook. Pulls every competitor's active Meta ads, diffs against last week, classifies new creative by emotional tone + messaging theme + funnel stage + format, and tells the strategist where the client should test next.

This replaces the generic `/spy` from external playbooks with one that uses:
- **HQ Ad Recon** (`list_recon_brands`, `list_recon_ads`, `get_recon_ad`, `get_recon_brand_analytics`) — Jetfuel's internal Meta Ad Library scraper, already running on tracked brands
- **Meta MCP** (`meta_ad_library_search`) — public Ad Library fallback when a brand isn't yet in recon
- **JF taxonomies** — 12 themes, 4 tones, Andromeda 14-point lens

## Arguments

- Client name (must match an HQ client). Default: ask.
- `--competitors "Brand A, Brand B, Brand C"` — competitor names. Default: read `.claude/ops/jf-spy/config.json` → client → competitors, or infer from `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md`.
- `--lookback 7` — days since last pull for the diff window. Default: 7.
- `--save-baseline` — overwrite the prior pull with today's pull.
- `--country US` — Ad Library country code. Default: US.

## Steps

### 1. Load identity, config, client brief

- Read `.claude/me.md` for user identity. If missing → STOP and tell user to run `./setup.sh`.
- Read `.claude/ops/jf-spy/config.json` for competitor mappings, last-pull timestamps, recon brand IDs.
- Read `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md` for brand voice, target personas, what creative is working.
- Get today's date via `date` (PowerShell: `Get-Date`).

### 2. Resolve the client + competitor set

- `list_clients --search "{client}"` → confirm client_id.
- For each competitor name, check `.claude/ops/jf-spy/config.json` for recon `brand_id`. If unmapped, call `list_recon_brands --search "{competitor}"` and write back the ID.
- For competitors not in HQ recon, fall back to Meta MCP `meta_ad_library_search --search_terms "{competitor}" --ad_active_status ACTIVE --limit 50`.

### 3. Pull current ad set per competitor

For each competitor:

**HQ-tracked brands (preferred):**
```
list_recon_ads(brand_id={brand_id}, active_only=true, limit=200)
get_recon_brand_analytics(brand_id={brand_id})  # for activity baseline
```

**Untracked brands (Meta Ad Library fallback):**
```
meta_ad_library_search(
  search_terms="{brand_name}",
  ad_active_status="ACTIVE",
  ad_type="ALL",
  countries="US",
  limit=100,
)
```

If both fail and the brand is critical, instruct the user to add it via HQ recon onboarding (see `add_recon_brand` tool) — recon backfills 30-90 days of history once tracked.

### 4. Diff against last week

- Load `.claude/ops/jf-spy/baselines/{client-slug}.json` (initialize empty on first run).
- For each competitor, compute:
  - **New ads** (ad IDs in this pull, not in last pull) — these are launches worth analyzing.
  - **Stopped ads** (in last pull, not in this pull) — paused/winners-graduated, useful signal.
  - **Persistent ads** (in both, run length > 30d) — these are the winners; analyze structure.

### 5. Classify every NEW + PERSISTENT ad against JF taxonomies

Per ad, tag:

**12 Messaging Themes** (from `project_andromeda_audit_rubric.md`):
Benefit/Outcome · Problem/Pain · Social Proof (review-led) · Comparison · Educational · UGC/Testimonial · Founder Story · Offer/Promo · Ingredient/Science · Lifestyle · Scarcity/Seasonal · Listicle/Format-driven

**4 Emotional Tones** (from `blog-drafts/05-emotional-creative-fatigue.md`):
Assured · Worried · Inspired · Amused

**Funnel Stage**: TOFU · MOFU · BOFU

**Format**: static · UGC video · founder-led video · carousel · Reels/vertical · polished video · collection

**Andromeda flags** (per Edwin's playbook):
- Founder-led: yes/no (2-3x ROAS lift)
- Vertical 9:16: yes/no
- Run length: New (0-7d) · Testing (8-30d) · Winner (30d+)

### 6. Run JF gap analysis

Compare the client's *current* Meta creative mix (from `list_campaigns` + `get_campaign_detail` + `list_creative_ads` on the client's Meta platform) against the competitor pull.

Produce three tables:

**Theme coverage** — Client % vs Competitor avg %. Flag themes where:
- Client at 0% AND ≥2 competitors >15% → **Missing theme**
- Client over-concentrated >40% in one theme → **Andromeda compression risk**

**Tone diversity** — Client tone mix vs competitor mix. Apply JF rule: no single tone >50%; ≥3 of 4 tones present.

**Format mix** — Tag Andromeda priority (vertical/UGC/founder-led = HIGH). Flag if client is static-heavy.

### 7. Surface "Market Trends" (Andromeda signal)

- If ≥2 competitors launched ads in the same theme in the diff window → "Market Trend" tag.
- If ≥3 competitors are running founder-led video and the client has none → flag as **HIGH PRIORITY** (per JF playbook: founder-led drives 2-3x ROAS in 2026).

### 8. Generate the report

Write `.claude/ops/jf-spy/reports/{client-slug}-{YYYY-MM-DD}.md` with:

```
# /jf-spy — {Client Name} — {date}

## Diff Summary
- New ads this week: {n} across {n} competitors
- Stopped ads: {n}
- Winners (30d+): {n}

## Market Trends (≥2 competitors converging)
1. {theme/format} — running on: {competitors}, examples: {ad descriptions}
2. ...

## Gaps Your Client Is Missing
| Gap | Severity | Why It Matters | Suggested Test |

## New Competitor Ads (table)
| Competitor | Hook (first 8 words) | Theme | Tone | Funnel | Format | Run Length | Snapshot |

## Persistent Winners (>30d)
[ads that are still running — these are the references to study]

## Recommended Next Tests
[3-5 specific ad concepts for the client, each citing the gap + the competitor evidence + the JF emotional tone target]
```

Also output a Google Sheet via `mcp__google-workspace__create_spreadsheet` with the full ad inventory (one tab per competitor + one summary tab).

### 9. Save baseline

If `--save-baseline` (or first run), overwrite `.claude/ops/jf-spy/baselines/{client-slug}.json` with this pull.

### 10. Present in-conversation summary

Print a tight Edwin-voice summary:

```
{N} new competitor ads since last pull. {M} are converging on the same theme — {theme}. 
{client} has zero. Top gap: {gap}. Pitched 3 tests below; full report in Sheet.
```

End with: "Want me to draft the briefs for these tests, or kick to /jf-hooks for variations?"

## Important Rules

- **Never fabricate ad creative.** If recon returns nothing and Meta Ad Library fails, label the competitor `[NO ACTIVE ADS FOUND]` — do not invent.
- **Never assign performance metrics to competitor ads** — Ad Library doesn't show them, recon doesn't either. Only the client's own ads have spend/ROAS.
- **All recommended tests must respect the client brief.** Brand voice, approved claims, founder availability, no off-strategy angles.
- **Andromeda lens is non-negotiable.** Every gap framing must reference whether the missing piece would help with theme diversity, tone diversity, format diversity, or volume — the four Andromeda levers.
- **No lookalike-era language.** Never recommend interest-stacking or "3% lookalike" tests as the answer.
- **First-pull is not a diff** — print "First run — establishing baseline" and skip the diff section.
- **Display all times in user's timezone** (from me.md).
- **The Google Sheet is the deliverable.** Conversation summary is a preview.

## Config

`.claude/ops/jf-spy/config.json`:

```json
{
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "competitors": [
        {"name": "Whispering Angel", "recon_brand_id": null},
        {"name": "Miraval", "recon_brand_id": null}
      ],
      "country": "US",
      "default_lookback_days": 7
    }
  },
  "leaders_by_vertical": {
    "wine": ["Whispering Angel", "Josh Cellars"],
    "wellness": ["Athletic Greens", "Olipop", "Liquid I.V."],
    "food": ["Magic Spoon", "Graza", "Fishwife"]
  }
}
```

Pre-fill `recon_brand_id` as you discover them via `list_recon_brands`.

## Why this skill exists (the JF lens)

Generic `/spy` skills dump a list of competitor ads and call it intelligence. That's not useful. The Jetfuel version is built around **what we'd actually do with the data on a Tuesday morning huddle**: find the angles 2+ competitors are converging on, check whether the client has coverage there, and propose specific tests that respect the brand brief.

Anchored in:
- `project_andromeda_audit_rubric.md` (the 14-point lens)
- `feedback_meta_ads_2026.md` (no lookalikes, creative-as-targeting)
- `blog-drafts/02-andromeda-algorithm.md`, `05-emotional-creative-fatigue.md`
- `edwin-tone-guide.md` (Edwin's "what are we really strong at, what are competitors falling short" framing from the 3-bucket method)
