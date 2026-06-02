---
name: jf-hooks
description: "Jetfuel hook + copy variation generator. Takes a seed (winning ad or angle) and produces N copy variations across the JF 4 emotional tones, 12 messaging themes, and personas from the client brief — all run through Edwin's anti-AI-tells voice filter. Output is CSV-ready for Meta bulk upload or a brief manifest for /jf-bulk-creative. Use when the user says 'spin up hooks', 'generate copy variations', 'more hooks like this one', 'rewrite this angle 20 ways', 'hook bank', 'copy variants', or has a winning hook and needs more."
disable-model-invocation: true
---

# /jf-hooks — Hook + Copy Variation Engine (Jetfuel)

Generate copy variations from a seed hook. Unlike generic `/hooks` skills that throw PAS/BAB/AIDA frameworks at the wall, the JF version varies across the structural axes Andromeda actually cares about — emotional tone, messaging theme, persona — and enforces Edwin's voice from `edwin-tone-guide.md`.

## What "good variation" means at Jetfuel

Per `blog-drafts/02-andromeda-algorithm.md`: changing a headline word is not a variation. It's the same ad. The hook bank produced here varies across:

1. **Emotional tone** (4): Assured · Worried · Inspired · Amused
2. **Messaging theme** (12 canonical, from JOYRIDE audit): Benefit/Outcome · Problem/Pain · Social Proof · Comparison · Educational · UGC/Testimonial · Founder Story · Offer/Promo · Ingredient/Science · Lifestyle · Scarcity/Seasonal · Listicle
3. **Persona** (from client brief): each persona gets language register tuned to it
4. **Funnel stage** (3): TOFU · MOFU · BOFU
5. **Hook structure** (varies syntax): question · stat-led · imperative · narrative · pattern interrupt · comparison

Surface-level frameworks (PAS, BAB, AIDA) are used *inside* a tone/theme cell — they're not the variation axis.

## Arguments

- Client name. Default: ask.
- `--seed "..."` — winning hook or angle, in quotes (≥5 words). Required.
- `--count N` — number of variations. Default: 30.
- `--tones "Assured,Worried,Inspired,Amused"` — comma list. Default: all 4 with no single >40%.
- `--themes "..."` — comma from the 12 canonical themes. Default: best 5 for the client brief.
- `--personas "..."` — comma from client brief. Default: all personas.
- `--funnels "TOFU,MOFU,BOFU"` — Default: all 3.
- `--output csv|manifest|both` — CSV for Meta bulk upload, manifest for `/jf-bulk-creative`. Default: both.

## Steps

### 1. Load identity, brief, voice

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md` — brand voice, approved claims, personas, founder availability, prohibited words, current offer.
- Read `.claude/edwin-tone-guide.md` — the anti-AI-tells checklist, Edwin sample voice for comparison.
- Read `.claude/ops/jf-hooks/config.json` for character limits per placement.

### 2. Parse the seed

Extract:
- Core claim (the underlying promise — strip visuals/format)
- Implicit tone (which of the 4 is the seed in?)
- Implicit theme (which of the 12?)
- Implicit persona (from naming convention if it's an existing ad)
- Hook structure (question / stat / narrative / etc)

Example: seed `"Most skincare routines are making your skin worse"` → tone=Worried, theme=Problem/Pain + Comparison, structure=stat-led claim, persona=skincare-frustrated.

### 3. Build the variation matrix

Cells = tones × themes × personas × funnels. For `--count=30`, sample 30 cells such that:
- No single tone >40% (the JF emotional diversity rule)
- ≥3 of 4 tones present
- ≥4 of 12 themes touched
- All requested personas covered
- TOFU/MOFU/BOFU balanced (default: 40/30/30)

### 4. Generate per-cell

For each cell, generate one variation with:
- **Hook** (the first 5-8 words that stop the scroll — structurally different from seed)
- **Primary text** (Meta primary text, ≤125 chars for safety)
- **Headline** (≤40 chars)
- **Description** (≤30 chars, optional)
- **CTA** (Shop Now / Learn More / Sign Up / Get Yours — funnel-stage appropriate)

Variation rules (per tone):

**Assured** — proof, expert tone, low-arousal-positive. "Trusted by 50,000+. Backed by clinical results. The reason {persona} switched."

**Worried** — stakes, friction, what-you-don't-know. Lead with the cost of inaction. NOT fear-mongering — Edwin's voice is grounded, not theatrical.

**Inspired** — possibility, aspiration, founder/story. THIS IS THE DEFAULT TRAP per `05-emotional-creative-fatigue.md` — only use it when the matrix demands it; don't over-index.

**Amused** — pattern interrupt, dry humor, unexpected angle. Edwin's voice is dry-funny, not zany. ("Yeah, we tried that. It didn't work.")

### 5. Run the Edwin-voice filter

Per `edwin-tone-guide.md`, reject any variation containing:
- "Here's the thing", "Let that sink in", "Read that again", "The truth is", "Here's why this matters"
- Em-dashes used as punch-line connectors ("Most skincare routines fail — and here's why")
- Imperative closers directed at the reader ("Stop doing X. Start doing Y.")
- Symmetric 3-bullet structures
- Generic motivational speaker language

Replace with Edwin patterns: thinking-out-loud, real numbers, specific personas, forward-momentum endings, parenthetical asides.

### 6. Apply client brief claim filter

Every variation passes the approved-claims check:
- No medical/health claims unless approved (per client brief)
- No price/offer claims that don't match the current offer in the brief
- No founder references if `founder_available=false`
- No competitor name-checking unless brief approves it

### 7. Apply the Andromeda compression check

Group all variations by **core claim**. If >25% cluster on one claim, reject and regenerate the cluster. Same trap from `02-andromeda-algorithm.md`.

### 8. Tag each variation

Output each row with:
- `id`: `{Client}_{Tone}_{Persona}_{Funnel}_{Theme}_v{NN}` (matches `/jf-bulk-creative` naming)
- `tone`, `theme`, `persona`, `funnel`, `hook_structure`
- `awareness_match`: which funnel stage maps to this tone+theme
- `placement_recommendation`: Feed / Reels / Story / Carousel
- `seed_link`: reference to the seed (for traceability)

### 9. Output

**CSV** (`{output-dir}/{client}-hooks-{date}.csv`) — Meta-bulk-upload-ready:
```
ad_name, primary_text, headline, description, cta, tone, theme, persona, funnel, format_suggestion
```

**Manifest** (`{output-dir}/{client}-hooks-{date}.json`) — feeds straight into `/jf-bulk-creative` so each hook gets paired with visual direction + producer brief.

**Sheet** — optional `mcp__google-workspace__create_spreadsheet` with the same data + a "Top 5 to test first" tab (highest-diversity, brief-aligned picks).

### 10. Present in-conversation summary

```
{N} hooks generated from seed. Distribution: {tone breakdown}, {theme coverage}, {funnel split}.
Edwin-voice filter: {pass/fail per variation}. Compression check: PASS.
Top 5 to test first: [list with IDs]
CSV: {path}. Manifest: {path}.

Next: /jf-bulk-creative --client={client} --use-manifest={manifest_path} to pair these with visuals.
```

## Important Rules

- **Structural variation, not surface.** Different word order ≠ variation. Different tone × theme × persona = variation. (`02-andromeda-algorithm.md`)
- **No AI tells.** Hard filter from `edwin-tone-guide.md`. Reject and retry, don't ship.
- **No emdash punch-line.** Per `feedback_content_voice.md` and `feedback_proposal_deck_voice.md`. Plain periods.
- **No over-indexed Inspired tone.** Inspired is the default trap that creates emotional monotony (`05-emotional-creative-fatigue.md`). Cap at 30% even when the seed is Inspired.
- **Respect approved claims.** Brief is law. No upgrading "supports digestion" to "cures bloat."
- **Founder availability gate.** If `founder_available=false`, no founder-led variations. Period.
- **Andromeda compression check is mandatory** before outputting. Don't ship 30 variations of one claim.
- **Character limits enforced.** Primary text ≤125 (safe), headline ≤40, description ≤30. RSAs/Meta truncate beyond.
- **Naming convention is the audit trail.** Every id must match `{Client}_{Tone}_{Persona}_{Funnel}_{Theme}_v{NN}` for `/jf-fatigue-scan` to slice later.
- **Display all times in user's timezone.**

## Config

`.claude/ops/jf-hooks/config.json`:

```json
{
  "defaults": {
    "count": 30,
    "max_single_tone_pct": 40,
    "min_tones_present": 3,
    "min_themes_present": 4,
    "funnel_default_mix": {"TOFU": 40, "MOFU": 30, "BOFU": 30}
  },
  "limits": {
    "primary_text_chars": 125,
    "headline_chars": 40,
    "description_chars": 30
  },
  "voice_filter": {
    "banned_phrases": [
      "Here's the thing",
      "Let that sink in",
      "Read that again",
      "The truth is",
      "Here's why this matters",
      "That's it.",
      "Let me explain"
    ],
    "banned_emdash_patterns": [
      " — and ",
      " — but ",
      " — here's "
    ]
  }
}
```

## Why this skill exists

External `/hooks` generates variations across PAS/BAB/AIDA frameworks. That made sense pre-Andromeda. Now those are surface variations — Meta groups them as one ad. The JF version varies across the axes Andromeda *actually* cares about (tone, theme, persona, funnel), enforces Edwin's voice (anti-AI-tells), and produces output that feeds cleanly into `/jf-bulk-creative` and `/jf-deploy-ads`.

Anchored in `edwin-tone-guide.md`, `blog-drafts/02-andromeda-algorithm.md`, `blog-drafts/05-emotional-creative-fatigue.md`, `project_andromeda_audit_rubric.md`, `feedback_content_voice.md`.
