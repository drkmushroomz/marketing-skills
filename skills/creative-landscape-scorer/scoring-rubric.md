# Andromeda 6-Dim Scoring Rubric

Encoded from the Meta Andromeda 2026 algorithm (https://adsuploader.com/blog/meta-andromeda) and Jetfuel's internal creative course. Use this as the scoring lookup when running the `creative-landscape-scorer` skill.

---

## How Andromeda actually works (one paragraph)

Meta's Andromeda is the **retrieval stage** that pre-filters billions of ads down to ~1,000 candidates within 300 milliseconds, before the auction. It builds a hierarchical decision tree using semantic similarity (computer vision on creative + NLP on copy + audio analysis) and clusters near-identical ads into a single "Entity ID." Two ads that share the same Entity ID compete with each other inside Andromeda, not against the rest of the market. So the question is no longer "how good is my ad" — it's "how many distinct Entity IDs am I getting to fan out across the tree."

Critically: aspect-ratio variations, color tweaks, text-only edits, and same-template ads all collapse into **one Entity ID**. Only creative that meaningfully varies across at least 2 of {Format, Persona, Environment, Benefit} creates a *new* Entity ID.

---

## Dimension 1: Entity ID Diversity (0–10)

**What we're measuring:** How many genuinely-distinct visual concepts the brand is fielding, and how those concepts spread across persona + benefit branches.

**Andromeda target:** 10–15 Entity IDs covering 3–5 personas, with each concept varying on ≥2 of: Format / Persona / Environment / Benefit.

### How to score from an Ad Library scrape

1. Group ads by visual similarity (do the cards look the same? same spokesperson? same setting?). Same-template ads = 1 Entity ID regardless of count.
2. For each group, classify across the 4 dimensions:
   - **Format:** static image / video-reel / carousel / story / motion-graphic / cinematic-studio / UGC-handheld
   - **Persona:** student / mom / professional / retiree / athlete / chef / host / foodie / etc. — pull from observable casting + framing
   - **Environment:** outdoors / office / home / gym / kitchen / restaurant / studio / social-setting
   - **Benefit:** save-money / save-time / status-identity / health / convenience / connection / sensory-pleasure / nostalgia
3. Count the distinct Entity IDs. Check persona spread.

### Score band

| Score | Pattern |
|---|---|
| 9–10 | 10+ Entity IDs, 3+ personas, 2+ formats, varied environments and benefits |
| 7–8 | 6–9 Entity IDs, 2–3 personas, 2 formats, some variation across other dims |
| 5–6 | 3–5 Entity IDs, 1–2 personas, mixed but limited variation |
| 3–4 | 2–3 Entity IDs from same template — high ad *count* hiding low diversity |
| 0–2 | 1 Entity ID across all ads (e.g. 30 hook variations of one video) |

### What kills the score
- "Fake diversity": 50 versions of one video with different opening hooks = 1 Entity ID
- All UGC, same creator, same kitchen, same product close-up = 1 Entity ID
- Aspect ratio exports counted as variants = no Entity ID gain

---

## Dimension 2: Targeting Breadth (0–10)

**What we're measuring:** Whether the account is structured to let Andromeda do its job (broad + creative-as-targeting) or fighting it (narrow interests, lookalikes, demographic gates).

**Andromeda mandate:** Broad targeting. Remove detailed interests. Remove lookalikes. Remove narrow demographics. Let creative diversity dictate audience.

### How to score from Ad Library (prospect mode)
We can't see audiences directly. Infer from observable signals:
- All ads run on all 5 placements (FB, IG, Audience Network, Messenger, Threads)? → broad placement ✓
- High creative diversity (Dim 1 ≥ 7) → indicates broad + creative-targeting strategy
- One ad obviously gendered, no obvious gendered counterpart → may indicate narrow demo targeting

### How to score in Client mode
Use HQ `list_creative_ads` with `columns=full` and inspect the targeting object. Flag any ad set with:
- `detailed_targeting` non-empty (interest gates)
- `custom_audiences` containing `lookalike` (LAL still in use)
- `age_min` > 18 or `age_max` < 65 without strong creative justification

### Score band

| Score | Pattern |
|---|---|
| 9–10 | All placements active, broad targeting, creative does the segmentation, no LAL |
| 7–8 | Mostly broad with occasional narrow tests |
| 5–6 | Mixed — half broad, half interest-gated |
| 3–4 | Mostly narrow interest stacks, LAL audiences in rotation |
| 0–2 | Heavy interest stacking, LAL-only, manual demographic fragmentation |

---

## Dimension 3: Budget Adequacy (0–10)

**What we're measuring:** Whether the budget is sufficient to exit learning per Entity ID.

**Andromeda min:** $50–100 per Entity ID per week to exit the 7–14 day / 50-event learning phase.

### Math
`min_weekly_budget = entity_id_count × $75` (midpoint)

Examples:
- 10 Entity IDs → $750/week minimum → $3,000/month
- 15 Entity IDs → $1,125/week → $4,500/month
- 20 Entity IDs on $500/week = fragmentation penalty (Andromeda anti-pattern)

### Only fully scorable in client mode
We can see spend in `creative_summary` / `creative_tag_analytics`. In prospect mode, we can sanity-check using their disclosed budget vs estimated Entity ID count (Dim 1).

### Score band

| Score | Pattern |
|---|---|
| 9–10 | Per-Entity-ID weekly spend ≥ $100 (clean exit from learning) |
| 7–8 | $50–100 (works but learning may extend) |
| 5–6 | $30–50 (fragmented but learning still possible on volume winners) |
| 3–4 | $15–30 (most Entity IDs stuck in learning) |
| 0–2 | <$15/Entity ID — budget can't pay for the diversity strategy |

---

## Dimension 4: Refresh Cadence (0–10)

**What we're measuring:** Whether new Entity IDs are being injected on a rolling basis (the right move) or one big batch is being run into the ground (creative fatigue).

**Andromeda implied target:** ~30% of active ads launched in the last 30 days, 50% in the last 60 days. Scale winners + add NEW variations of those specific concepts every 1–2 weeks.

### How to score
From Ad Library scrape, bucket `ad_delivery_start_time` of all active ads:
- < 30 days old
- 30–60 days
- 60–90 days
- > 90 days

### Score band

| Score | Pattern |
|---|---|
| 9–10 | ≥30% < 30d, fresh batch every 2 weeks, oldest active ads still ROAS-justified |
| 7–8 | ≥20% < 30d, regular cadence, some long-evergreens |
| 5–6 | Most batch from 30–90d window, occasional refresh |
| 3–4 | Batched launches with long gaps, fatigue likely |
| 0–2 | All ads from one launch event 60+ days ago, no refresh |

### Flora Foods example (May 2026)
Most ads launched March 29 + April 14 (mid-Q2 batch). One ad from Sept 2025 still running (8 months — either an evergreen winner or forgotten). Score 7/10: regular cadence, healthy mix.

---

## Dimension 5: Data Signal (0–10)

**What we're measuring:** Whether Andromeda's optimization signal is high-fidelity (CAPI on, events firing, attribution chain healthy) or degraded (browser-only pixel, iOS 14.5 attribution gaps).

**Mandatory (post-iOS 14.5):** CAPI on, Pixel firing, key events deduped, GA4 cross-check.

### How to score from page source (prospect mode)
Grep the brand's homepage + 1 PDP HTML for:
- `fbq(` or `connect.facebook.net` → **browser-side Pixel firing**
- `accountID":"facebook-web-pixel-live"` in trekkie config (Shopify integration)
- **`facebookCapiEnabled":true` vs `false`** → server-side CAPI status (definitive)
- `gtag(` + `G-` measurement ID → GA4 present
- `AW-` Google Ads conversion ID → Google Ads conversion tag
- Any of: TikTok pixel, Snap, Pinterest tag

### Score band

| Score | Pattern |
|---|---|
| 9–10 | Pixel + CAPI + GA4 + Google Ads tag, key events deduped, all firing |
| 7–8 | Pixel + CAPI on, Google Ads tag, GA4 — some events not deduped |
| 5–6 | Pixel firing browser-side, **CAPI off** — degraded signal post-iOS-14.5 |
| 3–4 | Partial pixel, key events missing |
| 0–2 | No Pixel at all (or Pixel installed but no events firing) |

### Flora Foods example (May 2026)
Score 5/10: Shopify Web Pixel configured (`accountID: facebook-web-pixel-live`), GA4 active (G-L23267X625), Google Ads tag firing (AW-11562461848), Klaviyo installed — but `facebookCapiEnabled: false`. The CAPI gap is the single biggest leak.

---

## Dimension 6: Vertical Coverage (0–10)

**What we're measuring:** How the brand's format mix compares to the top 3 organic competitors in their vertical — i.e., what creative formats their competitors are running that they aren't.

### How to score
1. Pull the brand's top 3 organic competitors from `mcp__ahrefs__site-explorer-organic-competitors`
2. Run an Ad Library scrape on each
3. Tag each competitor's creative across the **10 Creative Formats from Module 03** of the course:
   1. Studio product-shot
   2. UGC handheld testimonial
   3. UGC compilation / mashup
   4. Founder-led / authority
   5. Before/after / transformation
   6. Customer review / star rating
   7. Comparison / vs-competitor
   8. Educational / explainer
   9. Listicle / "5 reasons why"
   10. Lifestyle / aspirational
4. Same for the 10 UGC Strategies (from Module 03) when scoring UGC depth
5. Cross-ref against the 16 Human Desires (Module 04) — which desires is the brand hitting, which are competitors hitting that the brand isn't

### Score band

| Score | Pattern |
|---|---|
| 9–10 | Brand covers 8+/10 Formats and 12+/16 Desires; matches or exceeds competitor mix |
| 7–8 | Covers 6–7/10 Formats, missing 1–2 high-impact UGC strategies competitors are using |
| 5–6 | Covers 4–5/10 Formats — clear gaps competitors are exploiting |
| 3–4 | Covers 2–3/10 Formats — narrow strategic footprint |
| 0–2 | One format dominant, competitors operating in a different creative universe |

### Gap output template
For each missing format/strategy/desire, write: "Competitor X is running [Format Y] for [Desire Z]. We're not. Adding 2–3 Entity IDs in this format would close the gap."

---

## Content Gap Cross-Reference Tables

### The 10 Creative Formats (Module 03 anchor)
Source: course module `1Y4nYDq-zxwfz84NARaS5wahn-Fq2VCBs` → "02-The 10 Creative Formats to Test First"

When scoring, ask: which of these 10 formats does the brand have *zero* coverage on? Each absent format is a gap.

### The 10 UGC Strategies (Module 03 anchor)
Source: same folder → "03-10 UGC Strategies That Convert" (RTF + scripts spreadsheet)

When scoring UGC-heavy brands: which UGC angles are missing? Stitched testimonials, before/after, in-the-moment use, problem-solution, comparison, etc.

### The 16 Human Desires (Module 04 anchor)
Source: course module `1X-NHqVA6ny0qXXRJPSqONjt-p4oxd1Xz` → "02-The 16 Human Desires"

Cabell's 16: status, romance, social contact, family, vengeance, idealism, eating, physical activity, tranquility, saving, order, honor, power, curiosity, independence, acceptance.

When scoring food/CPG brands: most ads hit *eating* + *family* + *status*. The gap-finder is: which of the other 13 desires are competitors using? (E.g. *tranquility* for evening-pasta routine ads, *saving* for bundle value ads, *honor* for "authentic Italian heritage" ads.)

---

## Output formulas

### Composite score
`composite = (D1×0.25) + (D2×0.10) + (D3×0.10) + (D4×0.15) + (D5×0.20) + (D6×0.20)`

D1 (Entity ID Diversity) and D5 (Data Signal) are weighted heaviest because they're the two with the largest measured swing on Andromeda performance per the source article.

### Next-step ranking
For each identified gap or anti-pattern, tag:
- **Effort**: S (≤1 week), M (1–4 weeks), L (1+ month)
- **Impact**: S, M, L (judgment call grounded in dim weight)
- **Rank**: by Impact/Effort ratio descending

Output the top 5. Don't list more than 5 — long lists dilute focus. The 6th-onwards goes into "Future considerations" if needed.

---

## Anti-pattern catalog (auto-flag on detection)

| Symptom | Andromeda violation | Fix |
|---|---|---|
| 30+ ads with same template, different hooks | Fake diversity → 1 Entity ID | Build 3 truly distinct concepts per persona |
| Lookalike audiences in any active ad set | Targeting fragmentation | Remove LAL, go broad + creative |
| Interest stacks (3+ detailed interests) | Manual targeting conflicts with Andromeda | Strip to age/gender only |
| `facebookCapiEnabled: false` | Degraded signal | Turn on CAPI (1-day fix) |
| 1:1 + 4:5 + 9:16 of same creative counted as 3 ads | Aspect-ratio non-diversity | Count as 1 Entity ID, plan real new concepts |
| All ads launched > 60 days ago | No refresh cadence | Inject 3–4 new Entity IDs per 2-week sprint |
| No CTA variety (all "Shop Now") | Format under-experimentation | Test "Learn More", offer-specific CTAs |
| Welcome offer only in ad copy, not on site | Channel-conversion mismatch | Lift offer into Klaviyo welcome popup |
| Cold ads landing on homepage (not PDP/category) | LP optimization gap | PDP-specific landing pages (15–30% CVR lift) |
