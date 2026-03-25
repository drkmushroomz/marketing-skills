---
name: ad-copy-analyzer
description: Analyze Google Ads PPC ad copy and suggest improvements using direct-response + tastemaking principles
disable-model-invocation: true
---

# Ad Copy Analyzer

Analyze PPC ad copy for a Google Ads account and provide scoring + rewrite suggestions using a blended framework:
- **85% Direct Response** (AIDA from "Classified Ad Secrets") — drives conversions
- **15% Tastemaking** (STEPPS from "Contagious" by Jonah Berger) — drives shareability and engagement

## Arguments

The user may specify:
- An account name (e.g., "barker-wellness", "train-with-dave"). Default: ask.
- A campaign ID to narrow the scope. Default: all campaigns.
- `--lookback N` days. Default: 90.

## Steps

1. **Load identity, settings, and client context:**
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/ops/ad-copy-analyzer/config.json` for account mappings.
   - **Read `.claude/ops/ad-copy-analyzer/client-briefs/{account}.md`** if it exists. This file contains client-specific context from meeting transcripts: brand voice, target audience, product details, competitive landscape, what creative is working/failing, and strategic rules. ALL rewrite suggestions must respect this context.
   - If no client brief exists, search Google Drive for meeting transcripts mentioning the client name, read them, extract the relevant context, and save a new brief to `.claude/ops/ad-copy-analyzer/client-briefs/{account}.md` for future runs.

2. **Run the analyzer script:**
   ```bash
   python .claude/ops/ad-copy-analyzer/ad_copy_analyzer.py --account {account} [--campaign-id {id}] [--lookback {days}]
   ```
   - Parse the JSON output. If an error is returned, show it and stop.
   - The script returns both `dr_score` (direct response) and `stepps_score` (tastemaking) per ad, blended into `overall_copy_score`.

3. **Present the scorecard:**

   For each ad (sorted worst-first), show:

   ### Ad: {campaign_name} → {ad_group_name}
   | Metric | Value |
   |--------|-------|
   | Impressions | {n} |
   | Clicks / CTR | {n} / {pct}% |
   | Conversions / Conv Rate | {n} / {pct}% |
   | CPA / ROAS | ${n} / {n}x |
   | **Overall Score** | **{score}/100** (85% DR + 15% STEPPS) |
   | DR Score | {dr_score}/100 |
   | STEPPS Score | {stepps_score}/100 |
   | AIDA | {score}/4 — missing: {list} |
   | STEPPS | {count}/6 — missing: {list} |

   **Headlines** (score each):
   - "{headline}" — {score}/100 — {signals}

   **Descriptions** (score each):
   - "{description}" — {score}/100 — {signals}

   **Strengths:** {list}
   **Weaknesses:** {list}

4. **Generate rewrite suggestions:**

   For every ad scoring below 50, and for the bottom 5 ads regardless of score, generate rewrite suggestions. **All rewrites must respect the client brief** — use the brand voice, approved messaging hierarchy, known audience, and strategic context.

   **Blend:** Each rewrite should be primarily direct-response (AIDA) with a tastemaking element (STEPPS) woven in. The ratio is ~85/15 — the DR element drives the conversion, the STEPPS element makes it memorable/shareable.

   Use these rules from "Classified Ad Secrets" + "Contagious":

   **Headline Rewrites:**
   - Start with a strong attention-grabbing word (FREE, NEW, DISCOVER, SAVE, etc.)
   - Address the reader with "You/Your" when possible
   - Include a specific benefit, not a feature
   - Use numbers for specificity when relevant
   - Keep 15-30 chars (RSA headline limit is 30)
   - Match the AIDA element the headline is weakest on

   **Description Rewrites:**
   - Lead with the reader's benefit (what's in it for them)
   - Include at least one emotional trigger (social proof, guarantee, urgency, ease)
   - End with a clear call-to-action (Shop Now, Get Yours, Save Today)
   - Include guarantee/risk-reversal when the product supports it
   - Use "you/your" — never "we/our" as subject
   - Fill the space: aim for 70-90 chars (RSA description limit is 90)
   - Paint a mental picture of the outcome

   **The AIDA Checklist (every ad must have all 4):**
   - **Attention:** First headline must stop the scanner — power word, question, or shock
   - **Interest:** At least one headline/description states a clear benefit
   - **Desire:** Emotional trigger present — guarantee, social proof, urgency, or exclusivity
   - **Action:** At least one description ends with an explicit CTA

   **Psychological Triggers to Weave In:**
   - Scarcity: "Limited," "While supplies last," "Only X left"
   - Social proof: "Trusted by thousands," "Top-rated," "Best-selling"
   - Risk reversal: "Satisfaction guaranteed," "Free returns," "Risk-free"
   - Ease: "Easy," "Simple," "In minutes," "Hassle-free"
   - Curiosity: "Discover," "Secret," "The truth about," "Why"

   **STEPPS Tastemaking Layer (weave 1-2 into every rewrite):**

   - **Social Currency:** Make the reader feel like an insider. "What pros know," "The secret to," "Members-only," pattern-breaking claims.
   - **Triggers:** Link to daily cues the reader encounters. "Your morning routine + this," "Every Friday," time-of-day references.
   - **Emotion (HIGH-AROUSAL ONLY):** Awe, excitement, anger, anxiety, humor. NEVER low-arousal (calm, gentle, soothing as lead). Lead high-arousal, resolve into the calm benefit.
   - **Public / Social Proof:** Specific numbers: "50,000+ customers," "Rated 4.8 stars," "#1 in category." Peer behavior: "Your neighbors switched."
   - **Practical Value:** Rule of 100 (% off < $100, $ off > $100). Reference prices, scarcity ("Limit 2"), quantity limits, time limits.
   - **Stories:** Micro-narratives: "[Person] + [Problem] + [Product] + [Result]." Brand must be load-bearing (can't retell without naming it).

   **Client Context Rules (from client brief):**
   - Respect the brand voice — premium, accessible, athletic, aspirational. Not clinical.
   - Follow the messaging hierarchy: benefits first, ingredients second.
   - Don't make unapproved medical/health claims.
   - Reference the celebrity founder (Travis Barker) where appropriate for social currency.
   - Use approved offers (e.g., "25% off first order" if active, not made-up discounts).
   - Emphasize what Amazon can't offer (exclusives, bundles, subscriptions, DTC experience).
   - Weekend-specific urgency is effective for this audience.
   - Avoid contributing to ad fatigue — vary emotion, angle, format, and funnel stage across rewrites.

   Present rewrites as:
   ```
   ❌ Current: "{original}"  ({score}/100)
   ✅ Suggested: "{rewrite}"  (targets: {AIDA + STEPPS elements})
   ```

5. **Visual asset analysis:**

   The script also returns image and video assets. For each asset, download and visually inspect it using the Read tool (for images) or analyze the YouTube thumbnail.

   **Image Assets — evaluate against these criteria:**

   | Criterion | What to check | Common issues |
   |-----------|--------------|---------------|
   | **Text overlay legibility** | Can you read any text on the image at small sizes (300x250, 320x50)? | Text too small, low contrast against background, too many words |
   | **Visual hierarchy** | Is there a clear focal point? Does the eye flow: product → benefit → CTA? | Cluttered composition, no clear subject, competing elements |
   | **Product visibility** | Is the product clearly shown and recognizable? | Product too small, obscured, or missing entirely |
   | **Brand consistency** | Does it match the brand's color palette, typography, and tone? | Off-brand colors, inconsistent logo placement, mixed styles |
   | **Emotional resonance** | Does the image evoke the right feeling? (wellness = calm/natural, fitness = energy/aspiration) | Generic stock photos, no emotional connection, wrong mood |
   | **Aspect ratio coverage** | Are all required ratios present? (1.91:1 landscape, 1:1 square, 4:5 portrait) | Missing ratios = missed placements |
   | **Mobile-first clarity** | Does it work at mobile sizes? (most impressions are mobile) | Fine details lost at small sizes, text unreadable |
   | **CTA visibility** | If there's a button/CTA overlay, is it prominent? | CTA blends into background, too small, missing entirely |
   | **Lifestyle vs. product** | Is there a mix of product shots and lifestyle/in-use imagery? | All product-on-white = boring; all lifestyle = unclear what's sold |
   | **Color psychology** | Do colors support the message? Green=natural/health, Blue=trust, Red=urgency, Orange=energy | Colors conflict with brand or message |

   **Video Assets — evaluate thumbnails and metadata:**
   - Is the YouTube title compelling? (Apply headline scoring rules)
   - Does the thumbnail have a clear focal point and readable text?
   - Is the video title benefit-oriented or feature-oriented?
   - Flag videos with generic titles ("Product Demo", "Ad 1") as needing improvement

   **PMax Asset Groups — check completeness:**
   - Minimum required: 3 headlines, 2 long headlines, 1 description, 3 images (landscape + square + portrait), 1 logo
   - Recommended: 5+ headlines, 5+ descriptions, 5+ images per ratio, 1+ video
   - Flag any asset group below minimum as "incomplete — limiting delivery"
   - Score the text assets (headlines/descriptions) the same as RSA copy

   Present visual findings as:

   ### Visual Assets: {campaign_name}

   **Images ({count}):**
   For each image, after visually inspecting:
   - 🟢 / 🟡 / 🔴 {filename} — {width}x{height} ({aspect_ratio})
     - {visual assessment: what works, what doesn't}
     - Suggestion: {specific improvement}

   **Videos ({count}):**
   - {title} — [thumbnail assessment]
     - Title score: {apply headline scoring}/100
     - Suggestion: {improvement}

   **Asset Coverage Gaps:**
   - Missing aspect ratios
   - Missing asset types (no video, no lifestyle shots, etc.)
   - Below PMax minimums

6. **Summary section:**
   - Account-level average copy score
   - Count of ads missing each AIDA element
   - Top 3 most impactful changes (highest-impression ads with lowest scores)
   - Quick wins (easy fixes that could improve multiple ads)
   - Visual asset health: coverage gaps, quality flags
   - PMax asset group completeness summary

7. **Ask the user:**
   - "Want me to draft these changes in Google Ads Editor format (CSV)?"
   - "Want to focus on a specific campaign?"
   - "Want me to download and visually inspect specific images?"

## Scoring Reference

The scoring engine in `ad_copy_analyzer.py` rates headlines and descriptions 0-100 based on:

**Headlines (0-100):**
- Power/Yale-12 word density (up to 20 pts)
- Benefit orientation (up to 15 pts)
- "You/Your" usage (10 pts)
- Action/urgency words (up to 15 pts)
- Emotional triggers hit (up to 15 pts)
- Specificity — numbers/percentages (10 pts)
- Optimal length 15-30 chars (up to 10 pts)
- Penalty: self-centered language (-10 pts)
- Penalty: ALL CAPS (-5 pts)

**Descriptions (0-100):**
- Power/Yale word density (up to 15 pts)
- Benefit focus (up to 20 pts)
- "You/Your" usage (10 pts)
- Call-to-action present (15 pts)
- Emotional triggers (up to 15 pts)
- Guarantee/risk reversal (10 pts)
- Specificity (5 pts)
- Optimal length 60-90 chars (up to 10 pts)
- Penalty: self-centered language (-10 pts)

**AIDA Completeness (across full ad):**
- Attention: power words or Yale-12 present
- Interest: benefit indicators present
- Desire: emotional triggers present
- Action: CTA phrases present

**STEPPS Tastemaking Score (across full ad, 0-100):**
- Social Currency: insider/exclusive language, remarkable claims (up to 20 pts)
- Triggers: daily cue words — morning, routine, coffee, workout, etc. (up to 15 pts)
- Emotion: high-arousal positive — awe/excitement (up to 15 pts), high-arousal negative — anger/anxiety (up to 10 pts), PENALTY for low-arousal words (up to -10 pts)
- Public/Social Proof: specific customer numbers, ratings, peer behavior (up to 15 pts)
- Practical Value: deal framing, Rule of 100, scarcity signals (up to 15 pts)
- Stories/Narrative: story indicator words suggesting micro-narrative (up to 10 pts)

**STEPPS Completeness (across full ad):**
- Social Currency: insider/exclusive/remarkable language present
- Triggers: daily cue words present
- Emotion: high-arousal words present
- Public: social proof numbers or peer references present
- Practical Value: deal framing or useful-info signals present
- Stories: 2+ narrative indicator words present

**Overall Score = DR Score × 0.85 + STEPPS Score × 0.15**

## Client Briefs

Client briefs live in `.claude/ops/ad-copy-analyzer/client-briefs/{account}.md`. They contain:
- Brand identity and voice
- Product portfolio with SKU-level notes
- Target audience personas
- Competitive landscape
- Approved messaging hierarchy and content pillars
- What creative is working vs. failing (from meeting transcripts)
- Performance benchmarks and KPI targets
- Strategic rules (approved claims, pricing, promotions)

When a brief exists, ALL rewrite suggestions must be contextually appropriate. When no brief exists, search Google Drive for meeting transcripts, read them, extract relevant context, and create one.

## Notes
- Always present worst-scoring ads first — that's where the biggest improvement opportunity is
- When suggesting rewrites, maintain the product/brand voice from the client brief
- Keep RSA character limits: headlines ≤ 30 chars, descriptions ≤ 90 chars
- Never change the landing page URL — only analyze copy
- If performance data shows a low-scoring ad actually converts well, flag it as "scoring low but performing — may have brand-specific resonance"
- Conversely, high-scoring copy with poor CTR/conversion may indicate audience mismatch, not copy issues
- Lead with high-arousal hooks, resolve into the product benefit — don't let wellness brands fall into the low-arousal trap
- Vary rewrites across emotion, angle, format, and funnel stage to prevent ad fatigue
- Apply Rule of 100 for all offer framing: % off for products under $100, $ off for products over $100
