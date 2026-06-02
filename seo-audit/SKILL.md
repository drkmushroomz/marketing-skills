---
name: seo-audit
description: When the user wants to audit, review, or diagnose SEO issues on their site. Also use when the user mentions "SEO audit," "technical SEO," "why am I not ranking," "SEO issues," "on-page SEO," "meta tags review," "SEO health check," "my traffic dropped," "lost rankings," "not showing up in Google," "site isn't ranking," "Google update hit me," "page speed," "core web vitals," "crawl errors," or "indexing issues." Use this even if the user just says something vague like "my SEO is bad" or "help with SEO" — start with an audit. For building pages at scale to target keywords, see programmatic-seo. For adding structured data, see schema-markup. For AI search optimization, see ai-seo.
metadata:
  version: 1.3.0
---

# SEO Audit

You are an expert in search engine optimization. Your goal is to identify SEO issues and provide actionable recommendations to improve organic search performance.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing-context.md` exists (or `.claude/product-marketing-context.md` in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before auditing, understand:

1. **Site Context**
   - What type of site? (SaaS, e-commerce, blog, etc.)
   - What's the primary business goal for SEO?
   - What keywords/topics are priorities?

2. **Current State**
   - Any known issues or concerns?
   - Current organic traffic level?
   - Recent changes or migrations?

3. **Scope**
   - Full site audit or specific pages?
   - Technical + on-page, or one focus area?
   - Access to Search Console / analytics?

---

## Audit Framework

### Schema Markup Detection Limitation

**`web_fetch` and `curl` cannot reliably detect structured data / schema markup.**

Many CMS plugins (AIOSEO, Yoast, RankMath) inject JSON-LD via client-side JavaScript — it won't appear in static HTML or `web_fetch` output (which strips `<script>` tags during conversion).

**To accurately check for schema markup, use one of these methods:**
1. **Browser tool** — render the page and run: `document.querySelectorAll('script[type="application/ld+json"]')`
2. **Google Rich Results Test** — https://search.google.com/test/rich-results
3. **Screaming Frog export** — if the client provides one, use it (SF renders JavaScript)

Reporting "no schema found" based solely on `web_fetch` or `curl` leads to false audit findings — these tools can't see JS-injected schema.

### URL Existence Verification (before flagging anything as 404 or "missing page")

**A bare `curl -I` returning 404 does NOT prove a page is missing.** CMS platforms (especially Shopify) commonly:
- Route legacy URLs through URL Redirects that only fire with browser headers/cookies — invisible to `curl -I`.
- Put product-like content at `/pages/<slug>` rather than `/products/<slug>` when the brand sells through retailers instead of DTC.
- Use JavaScript/storefront-side redirects that a raw HTTP HEAD never sees.

**Before reporting any URL as 404 or "missing," you MUST do all three checks:**

1. **Follow redirects with a browser-like request:**
   ```
   curl -sIL -A "Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36" \
        -H "Accept: text/html" "<url>" | grep -iE "^(HTTP|location)"
   ```
   Report the full redirect chain, not just the first status code.

2. **Search the sitemap for the concept by keyword, not the guessed slug:**
   ```
   curl -s <site>/sitemap.xml                        # find the sub-sitemaps
   curl -s <sub-sitemap-url> | grep -iE "<keyword>"  # search by concept
   ```
   Check `sitemap_products_*.xml` AND `sitemap_pages_*.xml` (and `_collections_`, `_blogs_`).

3. **Try the platform's alternate URL patterns:**
   - Shopify: `/products/<slug>` ↔ `/pages/<slug>` ↔ `/collections/<slug>`
   - Statamic: `/<collection>/<slug>` ↔ `/<slug>` (collections often mount at root; check `statamic-structures` for the actual route mount)
   - WordPress (legacy client sites): `/<slug>/` ↔ `/product/<slug>/` ↔ `/shop/<slug>/`
   - Framer/Webflow: trailing slash and case variants

**Shopify-specific rule:** If a brand sells through retailers and not DTC, their "product pages" will usually live at `/pages/<slug>` (CMS page) rather than `/products/<slug>` (Shopify product with checkout). Don't flag the `/products/` 404 — find the `/pages/` equivalent and audit *that* for Product/Offer schema depth. Example: `hamptonwaterwine.com` puts Hampton Water Rosé at `/pages/rose-wine`, not `/products/hampton-water-rose`.

**If after all three checks the page is genuinely missing, the finding must cite:** (a) the curl -L redirect trace, (b) the sitemap searches performed, (c) the alternate patterns tried. No finding survives without that evidence.

### Priority Order
1. **Crawlability & Indexation** (can Google find and index it?)
2. **Technical Foundations** (is the site fast and functional?)
3. **On-Page Optimization** (is content optimized?)
4. **Content Quality** (does it deserve to rank?)
5. **Authority & Links** (does it have credibility?)

---

## Technical SEO Audit

### Crawlability

**Robots.txt**
- Check for unintentional blocks
- Verify important pages allowed
- Check sitemap reference

**XML Sitemap**
- Exists and accessible
- Submitted to Search Console
- Contains only canonical, indexable URLs
- Updated regularly
- Proper formatting

**Site Architecture**
- Important pages within 3 clicks of homepage
- Logical hierarchy
- Internal linking structure
- No orphan pages

**Crawl Budget Issues** (for large sites)
- Parameterized URLs under control
- Faceted navigation handled properly
- Infinite scroll with pagination fallback
- Session IDs not in URLs

### Indexation

**Index Status**
- site:domain.com check
- Search Console coverage report
- Compare indexed vs. expected

**Indexation Issues**
- Noindex tags on important pages
- Canonicals pointing wrong direction
- Redirect chains/loops
- Soft 404s
- Duplicate content without canonicals

**Canonicalization**
- All pages have canonical tags
- Self-referencing canonicals on unique pages
- HTTP → HTTPS canonicals
- www vs. non-www consistency
- Trailing slash consistency

### Site Speed & Core Web Vitals

**Core Web Vitals**
- LCP (Largest Contentful Paint): < 2.5s
- INP (Interaction to Next Paint): < 200ms
- CLS (Cumulative Layout Shift): < 0.1

**Speed Factors**
- Server response time (TTFB)
- Image optimization
- JavaScript execution
- CSS delivery
- Caching headers
- CDN usage
- Font loading

**Tools**
- PageSpeed Insights
- WebPageTest
- Chrome DevTools
- Search Console Core Web Vitals report

### Mobile-Friendliness

- Responsive design (not separate m. site)
- Tap target sizes
- Viewport configured
- No horizontal scroll
- Same content as desktop
- Mobile-first indexing readiness

### Security & HTTPS

- HTTPS across entire site
- Valid SSL certificate
- No mixed content
- HTTP → HTTPS redirects
- HSTS header (bonus)

### URL Structure

- Readable, descriptive URLs
- Keywords in URLs where natural
- Consistent structure
- No unnecessary parameters
- Lowercase and hyphen-separated

---

## On-Page SEO Audit

### Title Tags

**Check for:**
- Unique titles for each page
- Primary keyword near beginning
- 50-60 characters (visible in SERP)
- Compelling and click-worthy
- Brand name placement (end, usually)

**Common issues:**
- Duplicate titles
- Too long (truncated)
- Too short (wasted opportunity)
- Keyword stuffing
- Missing entirely

### Meta Descriptions

**Check for:**
- Unique descriptions per page
- 150-160 characters
- Includes primary keyword
- Clear value proposition
- Call to action

**Common issues:**
- Duplicate descriptions
- Auto-generated garbage
- Too long/short
- No compelling reason to click

### Heading Structure

**Check for:**
- One H1 per page
- H1 contains primary keyword
- Logical hierarchy (H1 → H2 → H3)
- Headings describe content
- Not just for styling

**Common issues:**
- Multiple H1s
- Skip levels (H1 → H3)
- Headings used for styling only
- No H1 on page

### Content Optimization

**Primary Page Content**
- Keyword in first 100 words
- Related keywords naturally used
- Sufficient depth/length for topic
- Answers search intent
- Better than competitors

**Thin Content Issues**
- Pages with little unique content
- Tag/category pages with no value
- Doorway pages
- Duplicate or near-duplicate content

### Image Optimization

**Check for:**
- Descriptive file names
- Alt text on all images
- Alt text describes image
- Compressed file sizes
- Modern formats (WebP)
- Lazy loading implemented
- Responsive images

### Internal Linking

**Check for:**
- Important pages well-linked
- Descriptive anchor text
- Logical link relationships
- No broken internal links
- Reasonable link count per page

**Common issues:**
- Orphan pages (no internal links)
- Over-optimized anchor text
- Important pages buried
- Excessive footer/sidebar links

### Keyword Targeting

**Per Page**
- Clear primary keyword target
- Title, H1, URL aligned
- Content satisfies search intent
- Not competing with other pages (cannibalization)

**Site-Wide**
- Keyword mapping document
- No major gaps in coverage
- No keyword cannibalization
- Logical topical clusters

---

## Content Quality Assessment

### E-E-A-T Signals

**Experience**
- First-hand experience demonstrated
- Original insights/data
- Real examples and case studies

**Expertise**
- Author credentials visible
- Accurate, detailed information
- Properly sourced claims

**Authoritativeness**
- Recognized in the space
- Cited by others
- Industry credentials

**Trustworthiness**
- Accurate information
- Transparent about business
- Contact information available
- Privacy policy, terms
- Secure site (HTTPS)

### Content Depth

- Comprehensive coverage of topic
- Answers follow-up questions
- Better than top-ranking competitors
- Updated and current

### User Engagement Signals

- Time on page
- Bounce rate in context
- Pages per session
- Return visits

---

## Common Issues by Site Type

### SaaS/Product Sites
- Product pages lack content depth
- Blog not integrated with product pages
- Missing comparison/alternative pages
- Feature pages thin on content
- No glossary/educational content

### E-commerce
- Thin category pages
- Duplicate product descriptions
- Missing product schema
- Faceted navigation creating duplicates
- Out-of-stock pages mishandled

### Content/Blog Sites
- Outdated content not refreshed
- Keyword cannibalization
- No topical clustering
- Poor internal linking
- Missing author pages

### Local Business
- Inconsistent NAP
- Missing local schema
- No Google Business Profile optimization
- Missing location pages
- No local content

---

## Output Format

### Audit Report Structure

**Executive Summary**
- Overall health assessment
- Top 3-5 priority issues
- Quick wins identified

**Technical SEO Findings**
For each issue:
- **Issue**: What's wrong
- **Impact**: SEO impact (High/Medium/Low)
- **Evidence**: How you found it
- **Fix**: Specific recommendation
- **Priority**: 1-5 or High/Medium/Low

**On-Page SEO Findings**
Same format as above

**Content Findings**
Same format as above

**Prioritized Action Plan**
1. Critical fixes (blocking indexation/ranking)
2. High-impact improvements
3. Quick wins (easy, immediate benefit)
4. Long-term recommendations

---

## References

- [AI Writing Detection](references/ai-writing-detection.md): Common AI writing patterns to avoid (em dashes, overused phrases, filler words)
- For AI search optimization (AEO, GEO, LLMO, AI Overviews), see the **ai-seo** skill

---

## Tools Referenced

**Free Tools**
- Google Search Console (essential)
- Google PageSpeed Insights
- Bing Webmaster Tools
- Rich Results Test (**use this for schema validation — it renders JavaScript**)
- Mobile-Friendly Test
- Schema Validator

> **Note on schema detection:** `web_fetch` strips `<script>` tags (including JSON-LD) and cannot detect JS-injected schema. Use the browser tool, Rich Results Test, or Screaming Frog instead — they render JavaScript and capture dynamically-injected markup. See the Schema Markup Detection Limitation section above.

**Paid Tools** (if available)
- Screaming Frog
- Ahrefs / Semrush
- Sitebulb
- ContentKing

---

## Task-Specific Questions

1. What pages/keywords matter most?
2. Do you have Search Console access?
3. Any recent changes or migrations?
4. Who are your top organic competitors?
5. What's your current organic traffic baseline?

---

## Jetfuel Field Playbook

How Jetfuel actually runs SEO audits and what has won for our clients. Apply this on top of the framework above. (Distilled from completed client audits, SEO call transcripts, and reporting docs: Hampton Water, Backyard Zip Line / Zip Line Gear, Grip Studs, Flora Fine Foods, Jinx, Aletha Health, Tate's Bake Shop, plus the "SEO Action Items" and ZLG SOW process docs in Drive.)

### Deliverable: the 5-section audit + 30/60/90 plan
Every JF audit converges on one structure. Fill all five sections before delivering, and model the format on the client audit docs above:
1. **Site Traffic Overview** — real GSC/GA4 baseline (clicks, impressions, CTR, avg position, sessions, YoY). Pull data, never estimate.
2. **Technical SEO Status** — crawlability, indexed-vs-expected count, 404/403, canonical issues, meta coverage.
3. **User Experience & Site Speed** — Core Web Vitals (LCP/INP/CLS), mobile.
4. **AI & GEO Overview** — schema coverage, FAQ schema, AI-bot access, brand citation presence, E-E-A-T signals.
5. **High-Level Action Plan** — phased 30/60/90 deliverables, then pitch a 120–190 day AIO phase as the retention layer.

Lead with an executive summary and an "Estimated Impact in 90 Days" stated as ranges and clearly labeled projections (e.g. "+20–40% organic impressions, first-ever AI citations"). Open with what is already working. Output is a Google Doc, often converted to a deck.

### Data discipline (hard rules)
- Pull real GSC + Ahrefs first. Use `[NEEDS REAL DATA]` placeholders rather than fabricate any metric, even anonymized.
- Verify every claim with primary evidence before it ships: raw HTML grep for tracking IDs, Ahrefs `is_spam` link-level flags, `curl -sIL` redirect traces for URL existence. The Hampton Water `/products/` 404 false-positive and the "no Pixel anywhere" false-negative are the canonical failure modes.
- Never recommend pausing existing paid spend in a proposal; frame foundation work as "in parallel."
- No em-dashes in any client-facing copy (top AI tell). See `references/ai-writing-detection.md`.

### Keyword & content diagnostics
- **Striking distance:** pull GSC positions 5–20 with impressions ≥ 20; prioritize by `impressions × (30 − position) / 30`.
- **Quick wins:** position 1–5 with CTR below 50% of expected (pos1≈30%, pos2≈15%, pos3≈10%) → title/meta rewrite.
- **Intent + cluster quality (Jinx model):** classify keywords transactional/informational/navigational and flag each content cluster HIGH / MIXED / LOW. High impressions + near-zero clicks = People Also Ask dead weight, not real traffic. Do not celebrate vanity impressions.
- **Keyword map in two tiers:** head terms (6–15 month marathon vs. major brands) separated from long-tail (visible jumps in weeks, higher intent). Each page gets exactly one job.
- **Content refresh triage (Orbit Media 22-pt):** Light (title/meta) / Medium (add 500–1,000 words + FAQ + tables) / Heavy (full rewrite at the same URL to preserve backlinks). Add a visible "last updated" date and `dateModified` in Article schema.

### AIO / GEO — a current diagnostic, not a future phase
- **FAQ schema is the #1 confirmed AIO lever.** ZLG went from zero ChatGPT mentions to being named 2–3× per response, with 93 AI-referred sessions and 4 conversions, after adding FAQPage schema to the homepage + FAQ page. Recommend FAQPage schema on homepage and key PDPs in every audit.
- **AI-bot access audit:** confirm robots.txt allows GPTBot, ChatGPT-User, OAI-SearchBot, PerplexityBot, ClaudeBot, anthropic-ai, Google-Extended, Bingbot. Blocking any = that engine cannot cite the brand. CCBot is training-only (safe to block). Cloudflare's "block AI bots" default silently blocks all of these.
- **Money prompts, not keywords:** test 30–50 conversational prompts written the way a frustrated buyer types them into ChatGPT (problem-first, with context and emotion), across the buyer funnel: Problem/Symptom → Buyer-Intent → Comparison/Validation → Authority. For each, record who gets cited and the content gap.
- **Dark SEO Funnel framing** for recommendations: Ingestion (schema, entity, original data) → Recommendation (surround-sound: G2/Capterra/Healthgrades/Trustpilot, Reddit/Quora, third-party press) → Verification (brand-SERP cleanup).
- **AIO readiness score (0–10) per priority page:** direct answer in opening paragraph (0–3), independently extractable H2 sections (0–2), FAQ with H3 question headings (0–2), comparison tables (0–1), Article + FAQPage schema (0–1), cited stats with source links (0–1). Below 5 = needs an AIO upgrade. Princeton GEO lifts: cite sources +40%, statistics +37%, quotations +30%, authoritative tone +25%; keyword stuffing −10%.
- **E-E-A-T for citations:** on-site press/media section with all PR linked, author bios with credentials, consistent brand facts, and direct "What is [Brand]?" / "Where to buy [Brand]?" answers in body copy. Usefulness beats volume: one calculator/quiz/tool (SoftwareApplication + FAQPage schema, placed outside any iframe) can outperform ten generic posts.
- **Track AI referral traffic** as its own GA4 segment and report AI-source conversions separately.

### Shopify / platform specifics
- **Dual-URL canonical trap:** post-migration sites keep both `/product/<slug>` (old) and `/products/<slug>` (new) live with no canonical, splitting equity. 301 the old, set canonical. Confirmed on Flora and ZLG.
- **Collection pages = programmatic SEO:** collection tags + dynamic H1/meta templates spin up long-tail purchase-intent pages ("100ft Zip Line Kits with Harness", "Kits under $200"). Manage crawl budget + canonical.
- **Reviews app schema:** wire Loox / Judge.me / Yotpo / Okendo star ratings into Product schema for SERP stars. Missing reviews = no rich result = CTR penalty.
- **Schema injection:** dynamic fields (price, stock) via GTM or Shopify metafields; validate with Rich Results Test (renders JS), never web_fetch.
- **Merchant Center:** submit YouTube videos as a supplemental feed for Shopping thumbnail visibility.
- **Indexation bloat:** filter/sort/tag pages inflate crawl; control via robots.txt + canonical.

### Recurring findings to always check
Unindexed pages at scale, 404s (GSC export → 301), 403 crawl waste, missing or over-160-char meta, canonical issues from migrations, duplicate content, stale sitemap (resubmit to GSC), toxic backlinks (`is_spam` → disavow), missing Open Graph, absent FAQ/Product/Article/Breadcrumb/Organization schema, no reviews app, no press section.

### Calibration (real JF results — for setting expectations, not for client decks without pulling the source)
ZLG: 61% YoY lift in top-3 keywords, 31% clicks / 35% impressions, AI citations from zero. Tate's: "gluten free cookies near me" 31 → top 10. These compounded over ~12 months; set the head-term timeline honestly.

---

## Related Skills

- **ai-seo**: For optimizing content for AI search engines (AEO, GEO, LLMO)
- **programmatic-seo**: For building SEO pages at scale
- **site-architecture**: For page hierarchy, navigation design, and URL structure
- **schema-markup**: For implementing structured data
- **page-cro**: For optimizing pages for conversion (not just ranking)
- **analytics-tracking**: For measuring SEO performance
