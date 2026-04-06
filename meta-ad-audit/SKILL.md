---
name: meta-ad-audit
description: "Audit a client's Meta (Facebook/Instagram) Ad Library against competitors in their vertical, identify messaging gaps, content gaps for target personas, and benchmark against e-commerce best practices. Use when the user mentions 'meta ad audit', 'facebook ad library', 'competitor ad analysis', 'ad library audit', 'meta creative audit', or 'social ad gaps'."
disable-model-invocation: true
---

# Meta Ad Library Audit

Audit a client's Meta ad creative against competitors and e-commerce best practices. Pulls the client's active Meta campaigns from HQ, scrapes the Meta Ad Library for competitor ads, categorizes every ad by messaging theme / funnel stage / format / offer type, and identifies specific gaps.

## Arguments

The user may specify:
- A client name (must match an HQ client). Default: ask.
- `--competitors "Brand A, Brand B, Brand C"` — competitor names to pull from Meta Ad Library. Default: infer from client brief or ask.
- `--vertical "category"` — e.g., "wellness", "fashion", "food & beverage", "home goods". Default: infer from client brief or ask.
- `--leaders` — also benchmark against 2-3 best-practice e-commerce brands (not direct competitors). Default: auto-select based on vertical.
- `--lookback N` days for HQ performance data. Default: 90.

## Steps

### 1. Load identity, settings, and client context

- Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
- Read `.claude/me.json` for user preferences.
- Read `.claude/ops/meta-ad-audit/config.json` for any saved competitor mappings and vertical defaults.
- **Read `.claude/ops/ad-copy-analyzer/client-briefs/{client-slug}.md`** if it exists. This file contains brand voice, target audience personas, product details, competitive landscape, and what creative is working/failing. If no brief exists, check Google Drive for meeting transcripts and create one.
- Get today's date via `date`.

### 2. Pull client's Meta ad data from HQ

Use HQ MCP tools to get the client's own Meta/Facebook ad data:

```
Step 2a: hq_list_clients → find client ID
Step 2b: hq_get_client_platforms → find their Meta/Facebook platform_id
Step 2c: hq_list_campaigns(platform_id, status="active") → all active Meta campaigns
Step 2d: For each campaign:
         - hq_get_campaign_detail(campaign_id, platform_type="facebook") → ad creative (title, body, images, videos)
         - hq_get_campaign_insights(campaign_id, platform_type="facebook", date_start, date_end) → performance metrics
```

Build a **Client Ad Inventory** with these fields per ad:
| Field | Source |
|-------|--------|
| Campaign name | hq_list_campaigns |
| Ad name / ID | hq_get_campaign_detail |
| Status | hq_get_campaign_detail |
| Headline / title | hq_get_campaign_detail |
| Primary text (body) | hq_get_campaign_detail |
| CTA button | hq_get_campaign_detail |
| Creative type (image/video/carousel) | hq_get_campaign_detail |
| Creative URL (poster/thumbnail) | hq_get_campaign_detail |
| Landing page URL | hq_get_campaign_detail |
| Impressions (lookback period) | hq_get_campaign_insights |
| Clicks / CTR | hq_get_campaign_insights |
| Conversions / Conv rate | hq_get_campaign_insights |
| Spend / CPA / ROAS | hq_get_campaign_insights |

### 3. Scrape competitor ads from Meta Ad Library

For each competitor (and best-practice leader), fetch their active ads from the Meta Ad Library.

**Method:** Use WebFetch to access the Meta Ad Library:
```
WebFetch URL: https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&q={competitor_name}&search_type=keyword_unordered
Prompt: "Extract all visible ads from this page. For each ad:
1) Advertiser name
2) Ad headline/title text
3) Primary text (body copy)
4) CTA button text
5) Creative type (image, video, carousel)
6) Whether it appears to be a product ad, lifestyle ad, testimonial, UGC, or brand awareness
7) Any visible offer (discount, free shipping, bundle, etc.)
8) Approximate start date if shown
9) Description of the visual creative (what's in the image/video thumbnail)
Return as structured data."
```

If WebFetch can't extract structured ad data from the Ad Library (it often requires JavaScript rendering), fall back to:
1. **WebSearch** for `site:facebook.com/ads/library "{competitor_name}"` to find direct ad library links
2. **WebSearch** for `"{competitor_name}" facebook ads examples` or `"{competitor_name}" meta ads` to find ad intelligence coverage (e.g., from Foreplay, AdSpy, Minea, or marketing blogs that screenshot competitor ads)
3. **WebFetch** any ad intelligence URLs found to extract creative examples

Also search for competitor ads covered in marketing case studies or roundups:
```
WebSearch: "{competitor_name}" facebook ad examples {year}
WebSearch: best {vertical} facebook ads {year}
WebSearch: {vertical} ecommerce ad creative examples
```

**For best-practice leaders**, use these defaults per vertical (or let the user override):

| Vertical | Best-Practice Leaders |
|----------|----------------------|
| Wellness / supplements | Athletic Greens (AG1), Liquid I.V., Olipop |
| Fashion / apparel | Gymshark, SKIMS, Alo Yoga |
| Food & beverage | Magic Spoon, Graza, Chamberlain Coffee |
| Home goods | Caraway, Our Place, Brooklinen |
| Beauty / skincare | Glossier, The Ordinary, Drunk Elephant |
| Fitness / training | Peloton, Tonal, Future |
| Pet | Farmer's Dog, Bark, Chewy |
| General e-commerce | refer to top DTC brands in the client's price range |

Build a **Competitor Ad Inventory** with the same messaging fields. Aim for 15-30 ads per competitor.

### 4. Categorize every ad by messaging taxonomy

Apply the following taxonomy to EVERY ad (client and competitor). An ad can have multiple tags.

#### 4A. Messaging Theme (primary hook)

| Theme | Description | Example hooks |
|-------|-------------|---------------|
| **Problem/Pain** | Leads with the problem the product solves | "Tired of...", "Struggling with...", "The problem with..." |
| **Benefit/Outcome** | Leads with the result or transformation | "Get [result] in [timeframe]", "Finally, [benefit]" |
| **Social Proof** | Leads with reviews, ratings, press, or celebrity | "50,000+ customers", "As seen in...", "Rated #1" |
| **UGC/Testimonial** | User-generated content or customer story | Customer video, unboxing, before/after |
| **Founder Story** | Brand origin, mission, or founder-led | "I created this because...", "Our founder..." |
| **Educational** | Teaches something, positions brand as expert | "Did you know...", "3 mistakes you're making..." |
| **Offer/Promo** | Leads with the deal | "40% off", "Buy 2 get 1", "Free shipping today" |
| **Scarcity/Urgency** | Time or quantity pressure | "Ends tonight", "Only 200 left", "Last chance" |
| **Comparison** | Us vs. them or old way vs. new way | "Unlike [competitor]...", "Stop using [old solution]" |
| **Lifestyle/Aspirational** | Aspirational imagery, no hard sell | Product in use, aesthetic lifestyle shot |
| **Unboxing/Product Demo** | Shows the product being opened or used | First-person POV, product close-ups |
| **Ingredient/Science** | Leads with formulation, ingredients, or R&D | "Powered by [ingredient]", "Clinically proven" |

#### 4B. Funnel Stage

| Stage | Signal |
|-------|--------|
| **TOFU (Awareness)** | Educational content, brand story, broad lifestyle |
| **MOFU (Consideration)** | Comparison, testimonials, product demos, ingredients |
| **BOFU (Conversion)** | Offer, urgency, retargeting copy ("Still thinking about..."), strong CTA |

#### 4C. Creative Format (2026 Andromeda-Optimized)

In 2026, Meta's Andromeda algorithm targets through creative, not audience settings. Format diversity is critical — Andromeda can evaluate 10,000x more ad variants simultaneously. Vertical, raw, social-native content is what Meta explicitly rewards.

| Format | What to tag | Andromeda Priority |
|--------|-------------|-------------------|
| Reel / vertical video (short) | Under 15 seconds, 9:16 | HIGH — Meta's preferred format |
| Reel / vertical video (medium) | 15-60 seconds, 9:16 | HIGH |
| UGC video | User/creator-filmed, raw feel | HIGH — outperforms polished 2-3x |
| Founder-led video | Founder speaking to camera | HIGH — 2-3x ROAS vs traditional |
| Carousel | Multi-image swipe | MEDIUM |
| Collection / Instant Experience | Full-screen mobile format | MEDIUM |
| Static image | Single image | MEDIUM — still needed for variety |
| Polished video | Studio/professional | LOW — underperforms native content |
| GIF / animation | Animated static | LOW |

#### 4D. Offer Type

| Offer | Examples |
|-------|----------|
| Percentage off | 20% off, up to 50% off |
| Dollar off | $10 off, Save $25 |
| Free shipping | Free shipping on orders $50+ |
| Bundle deal | Buy 2 get 1 free, Starter kit |
| Free gift | Free sample with purchase |
| Subscription discount | Subscribe & save 15% |
| No offer | Full price, value-prop only |

### 5. Gap analysis

Now compare the client's ad mix against competitors and best practices to find specific gaps.

#### 5A. Messaging Theme Gaps

Build a distribution table:

| Messaging Theme | Client (%) | Competitor 1 (%) | Competitor 2 (%) | Leaders Avg (%) | Gap? |
|-----------------|-----------|------------------|------------------|-----------------|------|

Flag themes where:
- Client has 0% but competitors or leaders have >15% → **Missing theme**
- Client has <10% but competitors average >25% → **Underweight theme**
- Client has >40% in a single theme → **Over-concentrated** (ad fatigue risk)

#### 5B. Funnel Stage Gaps

| Funnel Stage | Client (%) | Competitor Avg (%) | Leaders Avg (%) | Gap? |
|-------------|-----------|-------------------|-----------------|------|

Common gaps:
- All BOFU, no TOFU → "You're only talking to people ready to buy. No demand gen."
- All TOFU, no BOFU → "You're generating awareness but not closing. Need retargeting + offer ads."
- No MOFU → "Missing the consideration layer. People need proof before they buy."

#### 5C. Creative Format Gaps

| Format | Client (%) | Competitor Avg (%) | Leaders Avg (%) | Gap? |
|--------|-----------|-------------------|-----------------|------|

Flag:
- No video → "Video drives 2-3x engagement on Meta. Critical gap."
- No UGC → "UGC outperforms polished creative for DTC brands. Missing entirely."
- No carousel → "Carousels drive higher engagement for product education and storytelling."
- All static → "Static-only accounts underperform on Meta in 2024+."

#### 5D. Offer Strategy Gaps

| Offer Type | Client | Competitor 1 | Competitor 2 | Leaders |
|-----------|--------|-------------|-------------|---------|

Flag:
- Client never runs offers but all competitors do → "Competitors are offer-driven. Consider testing."
- Client only discounts but competitors use bundles/gifts → "Diversify offer strategy."
- No subscription push for replenishable products → "Missed LTV play."

#### 5E. Persona Coverage Gaps

Cross-reference the client brief's target personas against the messaging themes and creative:

For each persona in the client brief, check:
- Is there at least one ad that speaks directly to this persona's pain point?
- Is there creative showing someone who looks like this persona?
- Is the language register right for this persona (casual vs. professional, emotional vs. rational)?

Flag personas with zero dedicated ads.

#### 5F. Copy Quality Comparison

For each ad (client and competitor), score the primary text and headline using the same AIDA + STEPPS framework from the ad-copy-analyzer skill:

**Quick-score (0-10):**
- Power word in first 5 words? (+2)
- Clear benefit stated? (+2)
- Emotional trigger present? (+1)
- Social proof included? (+1)
- CTA present? (+1)
- Specific number/stat? (+1)
- "You/Your" language? (+1)
- Reads naturally (not keyword-stuffed)? (+1)

Compare average scores: client vs. competitors vs. leaders.

### 6. Best-practice benchmarking

Score the client's Meta ad program against these e-commerce best practices:

| Best Practice | Pass/Fail | Notes |
|--------------|-----------|-------|
| **Creative volume** — at least 15-20 active creatives in ASC | | |
| **Creative diversity** — at least 4 format types (Reel, UGC, static, carousel) | | |
| **Founder-led content** — founder/brand story video in the mix (2-3x ROAS in 2026) | | |
| **UGC in the mix** — at least 30% of ads are UGC/creator/founder content | | |
| **Vertical video** — at least 50% of video is 9:16 Reels/Stories format | | |
| **Messaging variety** — at least 4 themes represented | | |
| **Full-funnel coverage** — ASC (broad) + manual retargeting both present | | |
| **Hook variety** — first 3 words vary across ads (structural, not surface variation) | | |
| **Persona coverage** — each target persona has creative that self-selects them | | |
| **Social proof density** — press, reviews, or customer numbers in >25% of ads | | |
| **Retargeting layer** — manual campaign with funnel-stage messaging (15-20% budget) | | |
| **Campaign consolidation** — budget not fragmented across 5+ campaigns | | |
| **Learning phase health** — 50+ optimization events/week per ad set | | |
| **Ad refresh cadence** — 3+ new concepts launched per month | | |
| **Seasonal/timely creative** — ads reference current season, holiday, or trend | | |
| **Landing page variety** — ads link to different pages (not all to homepage) | | |

**Score: X/16.** Below 10 = significant gaps. Below 6 = program needs rebuilding.

### 7. Generate recommendations

Based on the gap analysis, produce specific, actionable recommendations:

#### Priority 1: Critical Gaps (things competitors all do that the client doesn't)
For each:
- What's missing
- Why it matters (with competitor evidence)
- Specific ad concept to fill the gap (headline + primary text + format + CTA)
- Which persona it targets
- Funnel stage

#### Priority 2: Competitive Advantages (things the client could own that competitors aren't doing)
- Identify messaging themes or angles NO competitor is using well
- Propose "blue ocean" ad concepts that differentiate

#### Priority 3: Creative Refresh List
- Which existing ads should be paused (high spend, low performance, stale)
- Which should be iterated (good concept, weak execution)
- New creative briefs for the top 5 gaps

**All ad concepts must respect the client brief** — brand voice, approved claims, messaging hierarchy, and strategic rules.

### 8. Output to Google Sheet

Create a Google Sheet using `mcp__google-workspace__create_spreadsheet` and `mcp__google-workspace__modify_sheet_values`.

#### Tab 1: "Client Ad Inventory"
All of the client's active Meta ads with categorization and performance.

| Campaign | Ad Name | Headline | Primary Text | Format | Theme | Funnel Stage | Offer | Impressions | CTR | Conv Rate | CPA | ROAS | Copy Score |

Sort by impressions descending.

#### Tab 2: "Competitor Ads"
All scraped competitor ads with categorization.

| Advertiser | Headline | Primary Text | Format | Theme | Funnel Stage | Offer | Creative Description | Source URL |

Group by advertiser.

#### Tab 3: "Messaging Gap Analysis"
The distribution comparison tables from Step 5A-5D.

#### Tab 4: "Persona Gaps"
Per-persona analysis from Step 5E.

| Persona | Pain Point | # Client Ads Targeting | # Competitor Ads Targeting | Gap Severity | Recommended Ad Concept |

#### Tab 5: "Best Practice Scorecard"
The 14-point checklist from Step 6.

| Best Practice | Client | Competitor 1 | Competitor 2 | Leader Avg | Status |

#### Tab 6: "Recommendations"
Prioritized action items from Step 7.

| Priority | Gap Type | What's Missing | Why It Matters | Ad Concept: Headline | Ad Concept: Primary Text | Format | CTA | Persona | Funnel Stage |

#### Tab 7: "Summary"
Executive overview.

| Metric | Value |
|--------|-------|
| Client ads analyzed | {n} |
| Competitors analyzed | {n} |
| Best-practice leaders analyzed | {n} |
| Best Practice Score | {x}/14 |
| Critical gaps found | {n} |
| Messaging themes missing | {list} |
| Funnel stages missing | {list} |
| Format gaps | {list} |
| Top 3 priority actions | {list} |
| Audit date | {date} |

### 9. Present summary in conversation

After writing the sheet, print:

```
## Meta Ad Library Audit — {Client Name}
Generated: {date}

### Your Ad Program: {n} active ads analyzed
- Best Practice Score: {x}/14
- Messaging themes: {n} of 12 used | Missing: {list}
- Funnel coverage: {TOFU/MOFU/BOFU breakdown}
- Format mix: {breakdown}
- Average copy score: {n}/10

### Competitor Landscape: {n} ads across {n} competitors
[Key takeaway about what competitors are doing that client isn't]

### Critical Gaps
1. {gap + why + what to do}
2. {gap + why + what to do}
3. {gap + why + what to do}

### Blue Ocean Opportunities
[Angles no competitor is using well that the client could own]

### Top 5 Actions
1. ...
2. ...
3. ...
4. ...
5. ...

Full report: [Google Sheet link]
```

### 10. Ask the user

- "Want me to write full creative briefs for the top gaps?"
- "Want to deep-dive on a specific competitor?"
- "Want me to score your existing ads with the full AIDA + STEPPS framework? (run `/ad-copy-analyzer` but for Meta)"

## Config

Config lives in `.claude/ops/meta-ad-audit/config.json`:

```json
{
  "verticals": {
    "wellness": {
      "leaders": ["Athletic Greens", "Liquid I.V.", "Olipop"],
      "common_competitors": []
    }
  },
  "clients": {
    "barker-wellness": {
      "vertical": "wellness",
      "competitors": ["Beam Organics", "Ned", "Charlotte's Web"],
      "meta_page_name": "Barker Wellness"
    }
  }
}
```

Competitors and leaders can be overridden via arguments.

## Important Rules

- **Never fabricate competitor ad data.** If you can't access a competitor's ads, say so. Use `[COULD NOT ACCESS — try manual check at fb.com/ads/library]` placeholders.
- **Never fabricate performance metrics.** Client metrics come from HQ only. Competitor ads have no performance data (Ad Library doesn't show it) — never estimate CTR/ROAS for competitors.
- **All ad concepts must respect the client brief.** Brand voice, approved claims, product positioning, and strategic rules apply to every recommendation.
- **Messaging taxonomy must be applied consistently.** Every ad gets tagged. Don't skip ads because they're hard to categorize — use the closest theme and note ambiguity.
- **Best-practice leaders are not competitors** — they're benchmarks for creative excellence. Make this distinction clear in the output. The client doesn't need to copy leaders, but should learn from their creative strategy.
- **The Meta Ad Library is public data.** No API keys needed. But it requires JavaScript rendering, so WebFetch may return incomplete data. Always have fallback search strategies.
- **Ad concepts are starting points, not final copy.** Label them as "Concept" not "Final." They need client review and brand approval before production.
- **Display all times in the user's timezone** (from me.md).
- **The Google Sheet is the deliverable.** The in-conversation summary is just a preview.
- **When composing any communication about bugs/issues with this skill, include the crew version.**
