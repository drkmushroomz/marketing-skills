---
name: presentation-zen
description: Use when auditing or tweaking a presentation deck (Google Slides, PowerPoint, PDF, Keynote) to apply Garr Reynolds' Presentation Zen design principles. Triggers on "audit this deck," "fix these slides," "make this presentation better," "apply Presentation Zen to," "review this pitch deck," "this deck looks bad / cluttered / wordy," or any request to improve slide design, simplify text-heavy slides, or critique visual hierarchy.
---

# Presentation Zen Deck Audit

Audit and tweak a presentation deck against Garr Reynolds' Presentation Zen principles. The goal is **maximum effect with minimum means** (*kanso*) — every slide should pass the billboard test (legible and graspable in three seconds from the back of the room).

## Inputs

The user will give you one of:
- A Google Slides URL or presentation ID → use `mcp__google-workspace__get_presentation` to read it
- A `.pptx` file path → read with `python-pptx` (available via `scripts/`) or extract slide XML
- A `.pdf` export → use `Read` (PDF supports up to 20 pages per call; loop in chunks)
- Screenshots → `Read` each image and treat each as one slide
- A description of slides → audit from the description, but flag that visuals weren't seen

If unclear which form, ask. If the deck is large (>20 slides), confirm whether to audit all slides or a sample (e.g. cover, key data slides, CTA, last slide).

## Read Before Auditing

**For Google Slides:** Always call `get_presentation` to get current slide content AND text indices. Per memory: Slides API has +1 hidden char per paragraph break — never reconstruct offsets, always read fresh before any `batch_update_presentation` call.

**For every slide, extract:**
- All text (title, body, footnotes, speaker notes if visible)
- Image count, position, and size relative to the slide
- Chart/table presence
- Background color and dominant text color

## The Audit Framework

Score each slide against these checks. Note violations; don't list passes.

### 1. Signal-to-Noise (highest priority)
- Is there one clear idea per slide? If two ideas → split.
- Remove: footers, page numbers on every slide, decorative shapes, drop shadows, gradients, every-slide logos, redundant labels, gridlines on charts, background watermarks.
- Each element must earn its place. "What can I delete?" beats "what can I add?"

### 2. The Billboard Test
- Can the audience grasp the slide in 3 seconds from the back of the room?
- Body text < 24pt → fail. Titles < 36pt → usually fail.
- Paragraphs of text → fail. Bullet lists more than 3-4 items → fail.

### 3. Slideuments
- If the slide reads like a document (sentences, dense bullets, "leave-behind" detail), it's a slideument.
- Slides support narration; documents are read alone. Don't try to do both — split into a deck + a separate handout.

### 4. Imagery
- Photos should be **large, often fullscreen**, not thumbnail-sized in a corner.
- One powerful image > four small ones.
- Stock-photo handshakes, generic "team meeting around laptop," abstract gradients, clip-art → flag and replace.
- Image quality: pixelated, low-res, watermarked, inconsistent style across deck → flag.

### 5. Layout & Composition
- **Rule of thirds:** main subject on a power point (intersection of thirds), not dead center.
- **Robin Williams' CRAP:** Contrast, Repetition, Alignment, Proximity. Misalignment by even a few px is the #1 amateur tell.
- White space is a feature, not a bug. Crammed slides fail. Empty space directs the eye.
- One dominant focal point per slide. If three things compete equally, the audience picks none.

### 6. Typography
- Sans-serif (or large slab serif) for projection. No Comic Sans, no Papyrus, no Times New Roman body text.
- Max 2 typefaces in the whole deck.
- Title ≥ 36pt, body ≥ 24pt, footnotes ≥ 18pt. Bigger is almost always better.
- Line length: aim for 6-9 words per line; never wrap a heading awkwardly.

### 7. Color
- Cool colors (blue, green) recede → backgrounds. Warm colors (orange, red) advance → emphasis.
- Bright room (most pitches/conferences): light background, dark text.
- Dark room (theater, demo): dark background, light text.
- Pick a 3-5 color palette and stick to it. Random accent colors per slide → fail.
- Contrast ratio: dark-on-dark and light-on-light are the most common defects. Per Edwin's standing rule, never ship dark-on-dark — flag every instance.

### 8. Charts & Data
- Title is a **declarative sentence**, not a label. "Revenue grew 38% YoY" not "Revenue."
- Restrain: drop the legend if one color suffices. Drop gridlines unless the value matters.
- Reduce: ink-to-data ratio — every pixel of chrome that isn't data is suspect.
- Emphasize: gray out everything except the one bar/line that proves the point.

### 9. Animation & Transitions
- Default to none. A "Wipe" or "Fade" sparingly is fine. "Fly," "Bounce," "Spin," 3D cube → never.
- Don't animate every bullet on every slide.
- Max 2-3 transition types across the entire deck.

### 10. Story Arc (deck-level, not slide-level)
- Does the deck open with a hook that makes the audience *care* (Andrew Stanton's principle)?
- Is there a single through-line, or is it a list of facts?
- Cover slide: does it tease the promise, or just state the company name?
- Closing slide: is there a memorable line/image, or just "Thank you / Q&A"?
- For pitch decks specifically: problem → audience → insight → solution → proof → ask.

## Output Format

Produce three sections:

### A. Executive Summary
- 2-3 sentences on overall state and the single biggest fix.
- Severity rating: **Ship-blocker / Major rework / Polish pass**.

### B. Slide-by-Slide Findings
A table with columns: `# | Slide title (or summary) | Violations | Recommended fix`.
Skip slides that pass cleanly. Don't pad.

### C. Deck-Level Issues
Things that aren't slide-specific: typography inconsistency, palette drift, no story arc, every-slide footers, etc.

### D. Prioritized Fix List
Numbered list, ordered by impact. Each item: what + which slides + how to do it.

## Applying Tweaks (when asked)

If the user says "apply the fixes" or "tweak it":

1. **Re-read the presentation** before any write — text offsets shift.
2. For Google Slides: use `mcp__google-workspace__batch_update_presentation` with explicit indices from the fresh read. Never reconstruct offsets manually.
3. **Make changes one batch per slide**, not one giant batch. Easier to revert.
4. After each batch, re-read that slide to confirm the change took.
5. For image swaps: ask the user for source images or generate placeholders — don't pull random stock without approval.
6. For text reduction: show the user the proposed new copy before deleting. Reducing wordy slides is destructive — confirm first.
7. For .pptx: use `python-pptx` via `scripts/` to make a copy, modify, and save with `_zen.pptx` suffix. Never overwrite the original.

## Voice for Slide Copy Rewrites

Per Edwin's content rules: plain conversational sentences, period-driven, no em-dash mid-sentence patterns, no copywriter punch, no AI tells (no "imagine," "unlock," "transform," "elevate," "in today's fast-paced world"). Headlines should sound like something Edwin would say out loud.

## Red Flags — Most Common Violations

| Symptom | Fix |
|---|---|
| Wall of bullets | Split into multiple slides; one idea each |
| Tiny chart in corner | Fullscreen the chart; gray out non-key data |
| Generic stock photo | Replace with concrete, specific image or remove |
| Footer/logo on every slide | Remove from all but cover and closing |
| Centered subject on every slide | Move to rule-of-thirds power point |
| Drop shadows everywhere | Strip all shadows |
| 5+ colors | Cut to 3 — one accent, two neutrals |
| Title in title case + body in sentence case | Pick one and apply throughout |
| "Thank you" closing slide | Replace with the memorable line or core CTA |
| Animated bullets | Disable, or replace with a build only when narratively necessary |

## When NOT to Apply Strict Zen

- Internal data review decks where dense tables are the *point*.
- Compliance/legal slides where every bullet is required.
- Engineering architecture deep-dives where the diagram IS the slide.
Note these explicitly in the audit so the user knows you're not blindly stripping content.
