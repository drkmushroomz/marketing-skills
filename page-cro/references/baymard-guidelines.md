# Baymard Institute CRO Guidelines

Research-backed conversion guidelines distilled from Baymard Institute's original usability studies. Use this when a page involves e-commerce, checkout, forms, product browsing, or mobile commerce — it replaces guesswork with documented test findings.

**Two layers of evidence here:**
1. **Free public benchmarks** (citable in client decks/audits — these are published on baymard.com).
2. **Licensed guideline sets** extracted from Baymard's full research reports (Checkout, Homepage & Category, M-Commerce). These are for internal analysis. Apply the *principles* in recommendations; do not republish the reports verbatim to clients.

## How to use this in a CRO audit
1. Identify the page/flow type, then jump to the matching guideline set below.
2. Triage by **severity**: fix **Harmful** issues first (they cause task abandonment), then Disruptive, then Interruption (minor individually, but collectively make a site feel "slow/tedious").
3. For e-commerce clients, cross-check the **Audit Priority Cheat Sheet** at the bottom first — those are the highest-leverage, most-commonly-violated guidelines.
4. Cite the **free public benchmarks** when you need an external number to justify a recommendation.

### Severity / Frequency scale (used throughout)
- **Severity:** Interruption (brief annoyance) < Disruptive (full stop, user must actively resolve) < Harmful (user cannot complete the task → abandonment).
- **Frequency:** A Few < Several < Most (>50%) < Nearly All < All. "% violated" figures come from Baymard's benchmark of the top-100 grossing US e-commerce sites.

---

## Free Public Benchmarks (citable)

**Cart / checkout abandonment**
- **70.22%** average documented cart abandonment (avg across 50 studies). The "holistic" 2024 checkout benchmark cites **69.80%**.
- Reasons users abandon (excl. the ~the "just browsing" segment): extra costs too high (shipping/tax/fees) **39%**, delivery too slow **21%**, didn't trust site with card **19%**, forced account creation **19%**, checkout too long/complicated **18%**, unsatisfactory returns policy **15%**, site errors/crashes **15%**, couldn't see total cost upfront **14%**, not enough payment methods **10%**, card declined **8%**.
- A large site can lift conversions **~35.26%** through checkout-design fixes alone; **~$260B** in lost orders is recoverable across US+EU via better checkout flow & design.

**Forms / checkout structure**
- Average checkout uses **~11.3 form fields**; Baymard says most sites need **≤8**.
- Average checkout is **~5 steps**, but "**perceived effort**" (how much work it feels like) matters more than raw step count.
- Half the top-100 sites pre-check the newsletter opt-in; ~a third silently force-subscribe.

**Pages & navigation (2025–26 benchmarks)**
- Product pages: **82%** of sites have severe UX issues; only **48%** rate "decent/good."
- Homepage & category navigation: **58%** of desktop and **67%** of mobile sites are "mediocre–poor." **95%** fail to highlight the user's current scope in main nav.
- Product lists: **58%** desktop / **78%** mobile are mediocre or worse.
- Mobile conversion runs **~half** of desktop; **43%** of mobile users abandoned a checkout in the past 2 months and **61%** sometimes/always switch to desktop to finish.

---

## 1. Checkout Guidelines (63)

*Source: "E-Commerce Checkout Usability." Desktop checkout, cart → completed order. % = top-100 benchmark violation rate.*

### Data Input (forms, validation, addresses)
- **Default shipping = billing address** (40% violated) — most people ship to their own home; cut fields and typos.
- **Ask for the same info only once** (45%) — never re-request data already given.
- **Indicate BOTH required and optional fields** (86%) — otherwise users leave required blank or overshare.
- **Preserve all input on validation errors** (10%) — never wipe entered data; re-typing drives abandonment.
- **Show input-format examples** (70%) — for phone, date, etc.
- **Use a single 'Name' field** (94%) — users type full name into "First name."
- **Validate inline** — as the user goes, not only on submit.
- **Remove single-option selects** (12%) — a one-item drop-down confuses.
- **Auto-detect city/state from ZIP** (90%) — >50% of subjects misspell city/state otherwise.
- **Disable paste on 'email confirmation' fields** (38%) — 60% paste, defeating the field.
- **Drop-downs only when <20 options** (95%) — big drop-downs are slow to scan.
- **Keep labels visible at all times** (3%) — no placeholder-only labels.
- **Geo-target smart defaults** — pre-select country, etc.
- **Add revealed fields BELOW the trigger field** (0%) — fields added above get missed (esp. 40+).
- **Field length should match expected input length** (30%).

### Copywriting (labels, buttons, errors)
- **Add descriptions to field labels** (63%) — 8/10 misunderstood at least one label; one abandoned.
- **Keep descriptions concise** (3%) — 9/10 skip long help text.
- **Explain 'special' features** (14%) — e.g. account activation.
- **Avoid technical jargon** (35%) — few understand "CVV2," etc.
- **Avoid contextual words like 'Continue…'** (62%) — ambiguous ("Continue Shopping" vs "Continue").
- **Clarify WHEN the charge happens** (44%) — users fear the primary button charges them early.
- **Use clear, meaningful shipping names** (28%) — not "EggSaver."
- **Format expiration-date field to match the card** (40%) — MM/YY.

### Layout (structure, hierarchy, visual design)
- **Use clear, unmissable error indications** (26%) — >half struggled to find/understand errors.
- **Make 'Guest checkout' the most prominent option** (14%) — 6/9 overlooked it when not visually dominant.
- **Single column for form fields** (17%) — two columns get seen as unrelated/overlooked; two subjects abandoned.
- **Style the primary action as a primary button** (38%) — users go by visual weight.
- **Curate options — avoid choice paralysis** (24%).
- **Use animation very cautiously** (0%) — distracting + reads as untrustworthy.
- **Reinforce sensitive (payment) fields with security cues** (89%) — half had security doubts at payment.
- **Use font size to signal hierarchy** (15%) — small fonts read as "unimportant."
- **Minimize clutter around checkout** (16%) — 7/10 slower on cluttered checkouts.
- **Show a sensible number of fields per screen** (19%) — 10–15+ intimidate.
- **Explain obscured fields** (52%) — e.g. why a value is masked.
- **Place the primary button in the expected spot / inside the form border** (21%).
- **Hide site navigation during checkout** (30%) — removes clutter and exit ramps.
- **Keep radio buttons in close proximity** (8%).
- **Use clever defaults to reduce friction** (9%).

### Navigation (cart, steps, the fold)
- **Let users force-proceed past imperfect validators** (5%) — address/ZIP validators are never perfect.
- **Provide text fallback for non-decorative images** (16%).
- **Drop-down carts persist while hovered** (10%).
- **Make process-step indicators clickable links** (40%).
- **Clearly show checkout steps** (17%).
- **Primary action/input above the fold** (20%).
- **Make icons clickable** (46%) — or users get disappointed.
- **Add hover/feedback states to actionable elements** (36%).

### Flow (sequence, costs, proceed buttons)
- **Keep checkout strictly linear** (3%) — no "steps within steps."
- **Show added costs clearly** (8%) — surprise fees are the #1 abandonment driver.
- **Don't use in-form 'Apply' buttons** (70%) — >half never click them or mistake them for the primary.
- **Show full/estimated price as early as possible** (31%).
- **Apply changes immediately and near the input** (27%).
- **Group criteria that need comparing** (28%) — e.g. shipping options together.
- **Visually separate pre-filled vs new fields** (13%).

### Focus (registration, cross-sell, coupons, privacy)
- **Make registration optional / offer guest checkout** (24%) — a third abandoned over forced accounts.
- **Newsletter opt-IN, not opt-out** (81%) — 32% of top sites silently force-subscribe.
- **Don't require seemingly unnecessary info** (61%) — e.g. phone number feels invasive.
- **Show only context-meaningful options** (13%).
- **Don't over-highlight the coupon field** (70%) — non-holders feel they're overpaying and leave to hunt codes.
- **Be careful with 'manage'/save features** (9%) — 6/9 didn't realize info was being saved.
- **Be careful cross-selling before the cart** (3%).
- **Be careful how you cross-sell in-cart** (24%) — relevant add-ons (cables, batteries) are tolerated.
- **Auto-accept 'close enough' address matches, with a manual fallback** (2%).
- **Auto-detect card type from the number** (71%) — don't make users pick Visa/MC.

---

## 2. Homepage, Category & Product-List Guidelines (79)

*Source: "E-Commerce Usability: Homepage & Category." Desktop browsing & product finding.*

### Homepage
- Feature a broad enough range of product types that first-timers can infer catalog breadth. **(Harmful)**
- Avoid ads / ad-looking content (and pop-ups/overlays) in prime homepage locations. **(Disruptive)**
- Carousels: auto-rotate (not too fast), pause on hover, stop permanently after interaction. **(Disruptive)**
- Help users pick a defined scope right from the homepage (popular categories, wizards). **(Disruptive)**
- Load search + main nav as the *first* elements. **(Interruption)**
- Use bespoke homepage imagery + great product photography (critical in visual industries). **(Disruptive)**
- Represent main nav / key sub-categories as homepage content if browsing is a key finding strategy.
- Personalize moderately and label changes; never customize core features. **(Disruptive)**
- Include at least one "inspirational" path.
- Default site scopes only pay off with a heavy audience overweight — use caution. **(Disruptive)**
- Make the search field immediately obvious (dominant on home, subdued elsewhere).

### Category Taxonomy
- Embed/promote wizards on the homepage. *(Stat: 8% discovery poorly placed vs 71% well-embedded.)*
- Seamless country/language selection; no overlay-dialog splash pages.
- Implement product type / brand / style as **filters, not categories**, when attributes are shared. **(Harmful)**
- Chunk categories: sub-divide near ~10; keep ≥10 products in the deepest level. **(Disruptive)**
- Watch for redundant/overlapping categories (esp. imported third-party categorization). **(Harmful)**
- Make category headers/groupings themselves selectable. **(Disruptive)**
- Provide compatibility-based list pages for compatibility-dependent products. **(Harmful — 65% gave up finding a compatible case.)**
- Nest "Accessories" sub-categories under high-level categories (don't dump them into the parent list). **(Disruptive)**
- Don't rely *solely* on thematic categories. **(Harmful — 75% of Gilt testers struggled.)**
- Use descriptive names, not jargon; keep naming consistent site-wide.
- Consider surfacing very popular filters in the category nav; consider a "What's New" category/filter.
- Avoid mixed category types in one group; consider placing a sub-category under multiple parents when valid.

### Main Navigation
- Main nav items = the top level of product categories, permanently visible. **(Harmful)**
- Visually reflect hierarchy (clickable group headers, font styling, indentation). **(Harmful)**
- Don't promote too-specific (sub-sub) categories in drop-downs. **(Harmful)**
- Hover drop-downs are OK but implement carefully (hover areas, delays). **(Disruptive)**
- Visually separate courtesy nav from product nav. **(Harmful)**
- Keep thematic categories in drop-downs separated and secondary.
- **Don't treat hover as consent to select** (25% had accidental hover-navigation). **(Disruptive)**
- Make main category options selectable and point to a page showing the same sub-categories.
- Add information scent (descriptions, tooltips, icons) in jargon-driven industries.
- Main drop-down should be accessible site-wide (checkout is an OK exception).
- Use a downward arrow / spatial indicator when only some nav items have drop-downs.

### Sub-Category Pages
- Make current scope abundantly clear by highlighting (only) the parent nav item. *(Only 55% deduced scope with weak highlighting.)*
- Implement first 1–2 hierarchy levels as sub-category pages, popular ones high with thumbnails. **(Harmful)**
- Category-leading thumbnails should crop heavily / show multiple products (so they aren't mistaken for one product). **(Harmful)**
- Don't split product lists into thematic sections or embed product sliders on category pages. **(Harmful)**
- Show & link sub-sub-categories for information scent.
- Add inspirational content + inline help; link inspirational images to all depicted products.

### Product Lists
- Each list item: price, name/type, thumbnail, variations + 1–2 industry attributes. **(Harmful)**
- Provide **all** the filters categories need (attributes, product-type, compatibility, status, user ranges). **(Harmful)**
- Design filtering so it isn't overlooked. **(Harmful — 40% failed to find filters; many mistook sorting for filtering.)**
- Default to **list-view** for spec-driven, **grid-view** for visual industries. **(Harmful)**
- Default "Relevance" sort with a diverse, representative first page. **(Harmful)**
- Support the common sort types meaningful to the site. **(Harmful)**
- Endless scroll + a "Load more" button after **50–100 products**. **(Interruption)**
- Show secondary attributes / repetitive controls only on hover; show a secondary thumbnail on hover.
- Avoid thumbnail ambiguity (recognizable product, no misleading crops, depict only what's included).
- Provide "View all"; attach range-interval indicators to pagination when sorting by attribute.
- Make "Customer Ratings" sort meaningful (weight by vote count or require a minimum).

### Site-Wide Layout
- No ads above product lists (graphical ads only below). **(Disruptive)**
- Be extremely cautious of account walls for browsing. **(Harmful — 89% didn't want to register at a wall.)**
- Direct return-policy link in the footer; cross-link from "Return an Item" tools.
- Divide footer links into semantic sections; provide a 2–3-level category sitemap.
- Ensure legibility of text over images (overlay or manual check; ~7% of users are color-blind).
- Don't show overlay dialogs on page load.

### Cross-Navigation & Cross-Selling
- Clarify whether one visual element leads to one path or many.
- Disable link styling/hover for links to the current page.
- Hierarchy breadcrumbs on all product pages + a history-based "Back to results" link. **(Disruptive)**
- Suggest both alternative AND supplementary products on the product page.
- Provide a "Recently viewed items" list; cross-link product collections back to their categories.
- Avoid content silos; logo always links home; consider a drop-down cart with model/specs.

---

## 3. Mobile / M-Commerce Guidelines (146)

*Source: "M-Commerce Usability" (2015 v1.2.4; a 2013 v1.1.0 edition is also in Drive). Applies to native apps too, except the Implementation chapter. Numbers in **bold** are concrete thresholds worth citing.*

### Concrete mobile thresholds (memorize these)
- Touch hit area: **≥ 7×7mm minimum**; spacing between tap targets **≥ 2mm**.
- Body font: **never below ~11pt**.
- List item height: **never > half the screen height** (portrait, ~500px); gallery images **≥ half screen width**.
- Build a **custom full-screen filter UI once you exceed 5 filter options**.
- Product titles in list items: **max 3–4 lines**.
- Cart: **2 checkout buttons when >3 items**, else 1.
- Text inside images: **3–5 words max**.
- Mandatory sort options: **Best Selling, Relevancy, Price**.
- Load indicators: show **immediately or within 1–2s** of a slow action.

### Understanding Mobile (foundation)
- Have **all** desktop content on mobile (full catalog + help pages). **(Harmful)**
- Always persist data; if you can't, warn before data loss. **(Harmful)**
- All links point to mobile-optimized pages; auto-redirect deep links to the matching mobile page.
- Be careful with "multiple stores in one"; keep features in the same scope as desktop.
- Reward every click with relevant, adequate content; button names set expectations (avoid contextual words).
- Clickability: spacing ≥2mm, functional icons, hit areas ≥7×7mm, one hit area per element, font ≥11pt.
- Context-aware: remove irrelevant options, set smart defaults, collapse single-option choices, auto-detect city/state from ZIP.
- Always provide an in-page escape route to the prior step. **(Harmful)**
- Distinct, unique primary-button styling; show consequences of selections immediately (no "Apply").
- Always have a "Full Site" link in the footer (95% of subjects went straight there). **(Harmful)**
- Make Policy/Terms approachable; surface real Shipping & Returns info in footer + on every product page.
- "Download App" / "Add to homescreen" dialogs: show once, never during checkout.

### Product Finding (mobile)
- Offer thematic/guided browsing (not just category nav + search). **(Harmful)**
- Be very cautious with carousels; never the only path to a feature. **(Harmful)**
- Easily scannable home/category pages (41% of homepages don't convey catalog type).
- Search: suggest relevant categories, offer "search within current category," handle misspellings AND synonyms, support thematic queries, always give alternatives on empty results. **(Harmful)**
- Product list: items ≤ half screen height, distinct hit area per item, large thumbnails, feature-rich item info, clear separation, gallery view for visual industries, "Load More" button, icons for jargon choices, indicate visited items, rows non-selectable.
- Filtering/sorting: always offer filters (even on search), keep Sort & Filter on one line, offer Best Selling/Relevancy/Price, auto-submit inline filters, show applied filters, allow multi-select/ranges, show match counts, in-stock filter, custom UI when >5 options (no drop-downs).
- Compatibility: list compatible products, show compatibility in overviews, be consistent with model names, offer relevant cross-sells (with title + thumbnail).

### Product Information (mobile)
- Don't serve product info/images on separate sub-pages. **(Harmful)**
- Collapsed content needs discrete sections + clear triggers; summarize reviews when >~5.
- Provide product-page breadcrumbs (88% of mobile sites lack them).
- Two primary buttons on the product page (incl. an "Add to Cart" at the bottom).
- Large product images, zoom/detail views, multiple angles, unambiguous variant images, honor swipe/tap/pinch gestures, scale proportionally in landscape.
- Adequate secondary specs (missing specs → rejection); bite-sized scannable descriptions; keep all specs in the spec list.
- Compatibility: image highlights compatibility, search understands model names, compatibility info on the product page.

### Checkout (mobile)
- Cart works as a "save" feature (persistence, product links, no forced checkout).
- Show "Order Total" **before** asking for card data (33% fail this). **(Harmful)** Offer a full price breakdown; never show fees below the total; no sneaky fees; hide coupon field behind a link.
- Show **both cost and speed** of all shipping methods; surface store availability/pickup; show cut-off time as a countdown.
- Always offer Guest Checkout, placed at the top (80% offer it but 88% hide/mis-design it; 60% of subjects struggled to find it). **(Harmful)**
- Newsletters opt-in, never opt-out.
- Keep flows strictly linear (never show the same page twice); provide "edit" wherever input is displayed.
- "Place Order" button at the very TOP of the Confirm Order page (users confuse it with "Order Confirmation"). Confirmation page shows order number + summary + email + arrival date.
- Show progress status; always provide a way to review the order; offer a map for physical locations.

### Data Input (mobile forms & keyboards)
- Hide redundant fields; ask info once; default billing = shipping; auto-detect card type; single name field (82% use 2+).
- **Labels above the field** (maximizes field width). **(Harmful)** Radio buttons close together; reposition labels in landscape; logical field sequence; section the form; verifiable day+date picker.
- Disable paste on email-confirm (or drop it); allow GPS + manual location; replace long drop-downs with auto-complete/IP geo; don't clear input on re-focus.
- Indicate required AND optional consistently (94% don't). **(Harmful)** Explain what's asked (tooltip); never inline labels; give formatting examples (60% don't); help for industry-specific options; labels understandable out of context; explain why "unnecessary" info is required (65% induce privacy concerns).
- Keyboards: format expiration to match card, one field per input entity (e.g. one phone field), disable auto-correct on weak-dictionary fields, show the right keyboard layout (only 46% do), honor Next/Previous, disable auto-capitalization on email/URL.
- Errors: say what's wrong + how to fix (92% use generic messages). **(Harmful)** Address validator that allows force-proceed; make errors instantly obvious; place errors next to the field; use front-end validation.

### Implementation (web-specific; N/A for native apps)
- Fast loads (minify/concat/compress/cache); non-blocking JS; lightweight after load; show load indicators within 1–2s.
- Client-side persistence (localStorage) for form input; fix layout & scrolling bugs; useful (not blank) error pages; ≤3–5 words of text in images; escape special characters in inputs/search.

---

## Audit Priority Cheat Sheet

When auditing an e-commerce page/flow, check these first — they're the highest-leverage, most-commonly-violated guidelines.

**Checkout — most-violated (top-100 benchmark):**
1. Drop-downs >20 options / single-option selects (95%)
2. Single name field (94%)
3. Auto-detect city/state from ZIP (90%)
4. Security cues on payment fields (89%)
5. Indicate required + optional fields (86%)
6. Newsletter opt-in not opt-out (81%)
7. Auto-detect card type (71%)
8. Input-format examples (70%)
9. No in-form 'Apply' buttons (70%)
10. Don't over-highlight coupon field (70%)

**Highest-severity (Harmful) themes to verify everywhere:**
- Forced account creation → always offer guest checkout (prominent, at top).
- Surprise costs → show all-in total before card entry; no hidden fees.
- Broken/unforgiving validation → preserve input on error; allow force-proceed past validators.
- Filtering that can't be found, or relying on thematic categories only.
- Account/registration walls blocking browsing.
- Mobile: missing content vs desktop, dead-end pages with no escape route, tiny tap targets (<7×7mm), labels not above fields.

**The four abandonment drivers to design against (free benchmark):** extra costs (39%), slow delivery (21%), card distrust (19%), forced account (19%). Every checkout audit should explicitly address all four.

---

*Sources: Baymard Institute research reports (E-Commerce Checkout Usability; Homepage & Category Usability; M-Commerce Usability) — licensed copies, internal use. Free benchmark figures from baymard.com (cart abandonment list, checkout/product-page/navigation benchmark articles). Report editions are 2013–2015; cross-check the live baymard.com benchmark for current percentages before citing specific numbers to clients.*
