# Publish Blog Post to Statamic

<role>
You publish blog content from Google Docs to jetfuel.agency as Statamic draft entries — with rich media, infographic-style visualizations, and a strong editorial structure.
</role>

<task>
Given a Google Doc (URL, ID, or name), read the content, transform it to a premium blog post with embedded rich media, custom visual elements, and a table-of-contents-driven structure, then publish as a draft via the Statamic MCP.
</task>

## Setup

1. Read config from `.claude/ops/publish-blog/config.json`
2. Publishing uses the `statamic` MCP server (`https://hq.jetfuel.agency/mcp/cms`). Auth is handled by the MCP — do not read passwords from `.claude/me.json`.
3. Google Docs access via `edwin@jetfuel.agency`

## Migration note (WordPress → Statamic)

jetfuel.agency migrated off WordPress. The old WP REST API, `scripts/wp_publish.py`, and app-password flow are deprecated. Before publishing, list the `statamic` MCP's tools to discover the correct names for: creating a draft entry, uploading an asset/image, setting featured image, setting taxonomy (categories/tags), and setting SEO metadata. Map the steps below to whatever the server actually exposes.

## Step 1: Read the Google Doc

Use `get_doc_as_markdown` MCP tool to pull the document content. If user provides a URL, extract the doc ID from it.

## Step 2: Build the Post Structure

**Prefer native Bard sets over inline-HTML blocks.** The `blog` collection's `content` field is a Bard with typed sets: `key_takeaways`, `toc`, `callout`, `stat_grid`, `comparison_table`, `faq_list`, `playbook_steps`, `pull_quote`, `cta_box`, `image`, `inline_stat`, `checklist`, `code_block`. Use these — they serialize to clean markdown for agent fetches, are token-cheaper than inline-styled HTML, and render consistently across the site theme. Inline-HTML templates below are a fallback for concepts Bard can't express.

Every post follows this editorial template:

### Post Template (top to bottom)

```
1. TITLE (H1) — pulled from doc
2. META BLOCK — author, date, reading time, category badges
3. KEY TAKEAWAYS BOX — 3-5 bullet summary at the very top
4. TABLE OF CONTENTS — auto-generated from H2/H3 headings, with anchor links
5. BODY SECTIONS — each H2 is a major section with:
   - Opening hook paragraph
   - Supporting content (paragraphs, lists, data)
   - VISUAL ELEMENT (infographic card, comparison table, stat highlight, or embedded media)
   - Section takeaway or transition
6. EXPERT TIP / CALLOUT BOXES — scattered throughout where relevant
7. FAQ SECTION — 3-5 questions with schema markup
8. CONCLUSION with CTA
9. RELATED POSTS suggestion
```

### Table of Contents Format

Generate a sticky-friendly TOC block at the top of the post:

```html
<div class="jf-toc" style="background:#f8f9fa; border-left:4px solid #ff6b35; padding:24px 28px; margin:32px 0; border-radius:8px;">
  <p style="font-weight:700; font-size:1.1em; margin:0 0 12px 0; color:#1a1a1a;">In This Article</p>
  <ul style="list-style:none; padding:0; margin:0;">
    <li style="margin:6px 0;"><a href="#section-slug" style="color:#ff6b35; text-decoration:none; font-weight:500;">Section Title</a></li>
    <!-- repeat for each H2 -->
  </ul>
</div>
```

Add matching `id` attributes to each `<h2>` in the body.

### Key Takeaways Box

Place at the top, before the TOC:

```html
<div class="jf-key-takeaways" style="background:linear-gradient(135deg, #fff5f0 0%, #fff 100%); border:2px solid #ff6b35; border-radius:12px; padding:28px 32px; margin:32px 0;">
  <p style="font-weight:800; font-size:1.15em; color:#ff6b35; margin:0 0 16px 0;">⚡ Key Takeaways</p>
  <ul style="margin:0; padding-left:20px; line-height:1.8;">
    <li><strong>Takeaway 1</strong> — supporting detail</li>
    <li><strong>Takeaway 2</strong> — supporting detail</li>
    <li><strong>Takeaway 3</strong> — supporting detail</li>
  </ul>
</div>
```

## Step 3: Rich Media Embedding

**Rule:** every H2 earns ONE structured element an agent can extract as data. Use the matching native Bard set first (stat_grid, comparison_table, callout, playbook_steps, pull_quote, faq_list, image, inline_stat). Only drop to the inline-HTML templates below when the Bard schema can't represent what you need.

### A. Stat Highlight Cards

For impressive numbers, metrics, or data points:

```html
<div style="display:flex; gap:16px; flex-wrap:wrap; margin:28px 0;">
  <div style="flex:1; min-width:200px; background:#1a1a1a; color:#fff; border-radius:12px; padding:24px; text-align:center;">
    <div style="font-size:2.4em; font-weight:800; color:#ff6b35; line-height:1;">288%</div>
    <div style="font-size:0.85em; margin-top:8px; opacity:0.8;">ROAS Increase</div>
  </div>
  <div style="flex:1; min-width:200px; background:#1a1a1a; color:#fff; border-radius:12px; padding:24px; text-align:center;">
    <div style="font-size:2.4em; font-weight:800; color:#ff6b35; line-height:1;">94%</div>
    <div style="font-size:0.85em; margin-top:8px; opacity:0.8;">Client Retention</div>
  </div>
</div>
```

### B. Comparison Tables (Polsia-style)

For side-by-side comparisons with visual indicators:

```html
<div style="overflow-x:auto; margin:28px 0;">
  <table style="width:100%; border-collapse:collapse; font-size:0.95em; border-radius:12px; overflow:hidden; background:#ffffff; color:#1a1a1a;">
    <thead>
      <tr style="background:#1a1a1a; color:#fff;">
        <th style="padding:14px 18px; text-align:left; font-weight:600;">Feature</th>
        <th style="padding:14px 18px; text-align:center; font-weight:600;">Option A</th>
        <th style="padding:14px 18px; text-align:center; font-weight:600;">Option B</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom:1px solid #eee;">
        <td style="color:#1a1a1a; padding:12px 18px; font-weight:500;">Feature Name</td>
        <td style="color:#1a1a1a; padding:12px 18px; text-align:center;">
          <span style="background:#e8f5e9; color:#2e7d32; padding:4px 12px; border-radius:20px; font-size:0.85em; font-weight:600;">✓ Strong</span>
        </td>
        <td style="color:#1a1a1a; padding:12px 18px; text-align:center;">
          <span style="background:#fff3e0; color:#e65100; padding:4px 12px; border-radius:20px; font-size:0.85em; font-weight:600;">~ Limited</span>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### C. Progress/Rating Bars

For scoring, benchmarks, or ranked lists:

```html
<div style="margin:28px 0;">
  <div style="margin:12px 0;">
    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
      <span style="font-weight:600; font-size:0.9em;">Meta Ads</span>
      <span style="font-weight:700; color:#ff6b35;">8.5/10</span>
    </div>
    <div style="background:#f0f0f0; border-radius:8px; height:10px; overflow:hidden;">
      <div style="background:linear-gradient(90deg, #ff6b35, #ff8f65); width:85%; height:100%; border-radius:8px;"></div>
    </div>
  </div>
  <!-- repeat for each item -->
</div>
```

### D. Callout / Pro Tip Boxes

For expert insights, warnings, or key information:

```html
<div style="background:#f0f7ff; border-left:4px solid #1976d2; border-radius:0 8px 8px 0; padding:20px 24px; margin:28px 0;">
  <p style="font-weight:700; color:#1976d2; margin:0 0 8px 0;">💡 Pro Tip</p>
  <p style="margin:0; line-height:1.7;">Tip content here with actionable advice.</p>
</div>
```

Variants:
- **Warning**: background `#fff8e1`, border `#f9a825`, icon ⚠️
- **Key Insight**: background `#f3e5f5`, border `#7b1fa2`, icon 🎯
- **Case Study**: background `#e8f5e9`, border `#2e7d32`, icon 📊

### E. Quote/Testimonial Blocks

```html
<div style="background:#fafafa; border-radius:12px; padding:28px 32px; margin:28px 0; position:relative;">
  <div style="font-size:3em; color:#ff6b35; position:absolute; top:12px; left:20px; opacity:0.3;">"</div>
  <p style="font-size:1.1em; font-style:italic; line-height:1.8; margin:0 0 12px 0; padding-left:24px;">Quote text here.</p>
  <p style="margin:0; padding-left:24px; font-weight:600; color:#666;">— Author Name, Title</p>
</div>
```

### F. Step-by-Step Process Visualization

For how-to content with numbered steps:

```html
<div style="margin:28px 0;">
  <div style="display:flex; align-items:flex-start; margin:20px 0;">
    <div style="min-width:48px; height:48px; background:#ff6b35; color:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1.2em; margin-right:16px;">1</div>
    <div>
      <p style="font-weight:700; margin:0 0 4px 0; font-size:1.05em;">Step Title</p>
      <p style="margin:0; color:#555; line-height:1.7;">Step description with actionable detail.</p>
    </div>
  </div>
  <!-- repeat for each step -->
</div>
```

### G. Embedded Rich Media

For external content, prefer Bard's native `image` set or, for YouTube/Twitter, drop to inline HTML inside a paragraph node:
- **YouTube**: `<figure><div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;"><iframe src="https://www.youtube.com/embed/VIDEO_ID" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen></iframe></div></figure>`
- **Twitter/X**: paste the tweet URL on its own line — Statamic's renderer auto-embeds where the theme supports it; otherwise use the official Twitter embed script
- **Images**: use the native Bard `image` set (uploads via `mcp__statamic__statamic-assets`) or `<figure><img src="URL" alt="descriptive alt text" /><figcaption>Caption text</figcaption></figure>`
- **Podcast clips**: Embed Spotify/Apple podcast player iframes

## Step 4: Visual Element Selection Rules

Choose visual elements based on content type:

| Content Type | Best Visual Element |
|---|---|
| Data/metrics/benchmarks | Stat Highlight Cards |
| Platform/tool/service comparison | Comparison Table (Polsia-style) |
| Rankings, scores, ratings | Progress/Rating Bars |
| Expert advice, warnings | Callout Boxes |
| Client results, testimonials | Quote Blocks |
| How-to, tutorials, processes | Step-by-Step Visualization |
| Related video/audio content | Embedded Rich Media |

**Minimum requirement: every H2 has one structured element (native Bard set preferred).**

## Step 5: FAQ Schema Section

Add a FAQ section before the conclusion with proper schema markup:

```html
<div itemscope itemtype="https://schema.org/FAQPage">
  <h2>Frequently Asked Questions</h2>
  <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
    <h3 itemprop="name">Question text?</h3>
    <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
      <p itemprop="text">Answer text.</p>
    </div>
  </div>
</div>
```

## Step 6: Set SEO Metadata

- **Title**: from the doc's H1 or first heading
- **Slug**: auto-generated from title (lowercase, hyphens, no stop words)
- **Categories**: match content to existing categories in config.json
- **Tags**: extract 3-8 relevant tags from content
- **Excerpt/Meta description**: first 155 chars of content or explicit excerpt
- **Author**: default to Edwin Choi (ID 1) unless specified
- **Status**: always `draft` unless user explicitly says publish

## Step 7: Publish via Statamic MCP

**MANDATORY: All CMS operations go through the native `mcp__statamic__*` tools available in Claude Code.** Do not write Python scripts that POST to `hq.jetfuel.agency/mcp/cms` with a bearer token — that bypasses the audited MCP path, hardcodes credentials in the working tree, and produced the 5/2 backlinks-post submission we have to clean up. If a step feels easier in a Python script, it's still wrong: invoke the MCP tool directly.

Workflow:

1. Read the `blog_post` blueprint first via `mcp__statamic__statamic-blueprints` (action=get) to confirm field handles and the Bard content schema.
2. **The `content` field is a Bard field (ProseMirror tree), not an HTML string.** Passing raw HTML wraps the whole payload as a single text node inside one paragraph — it renders as escaped markup. You must pass `content` as an array of ProseMirror nodes. Reuse `scripts/build_gemini_bard.py` as a *reference for the node shape only* — copy its helper functions into your in-conversation reasoning to assemble the JSON, then pass the resulting array directly to the MCP tool. Do not execute a script that performs the MCP call itself.
3. Create the entry as a **draft** (`published: false`) via `mcp__statamic__statamic-entries` (action=create) with: title, date (required — see caveat below), author (entry ID reference, looked up from `authors` collection), categories (term slug array), tags (term slug array), seo_title, seo_description, and the Bard `content` array.

   **Date timezone caveat (critical — gets entries 404ing if wrong):** The Statamic server runs on `America/Los_Angeles` (PDT = UTC-7). The MCP tool strips any timezone offset you pass and treats the time component as local Pacific time, then adds 7 hours when writing to disk. Passing a UTC timestamp with a `Z` suffix or `-07:00` offset does NOT work — the offset is ignored. To guarantee the entry is live-datable (never scheduled into the future), always format the date as `YYYY-MM-DDT00:00:00` with no timezone suffix, using today's Pacific date obtained from `date`. Midnight Pacific stores as `07:00:00Z` (7 AM UTC), which is always in the past during business hours. Example: `2026-05-11T00:00:00`. Do NOT pass a UTC wall-clock time — on a PDT server, `T15:00:00Z` becomes `T22:00:00Z` (10 PM Pacific), which is in the future until late evening.
4. Create missing taxonomy terms first via `mcp__statamic__statamic-terms` (action=create) if the category/tag you want doesn't exist. Term IDs are formatted `taxonomies::slug` but the entry's term field takes just the slug (`"ai-seo"`, not `"categories::ai-seo"`).
5. **Slug caveat:** Statamic derives the slug from the title on create and appears to ignore slug on update. If you want a short SEO slug, rename in the CP after create.
6. Capture the returned entry ID for Step 9.

Never hardcode credentials — auth is carried by the MCP connection. If you find yourself reaching for `urllib`, `requests`, or `Bearer` headers, stop and use the MCP tool.

## Step 8: Generate Featured Image

Every post MUST have a featured image matching the Jetfuel blog template. Use `scripts/generate_blog_image.py`:

```bash
python3 scripts/generate_blog_image.py \
  --title "Post Title Here" \
  --subtitle "Short Subtitle or Tagline" \
  --output scripts/featured_image.png
```

Optional: pass `--bg path/to/photo.jpg` for a custom background photo. Without it, uses the default stock image.

### Template style (must match existing blog posts):
- 1200x1200 square image
- Dark-tinted stock photo background (~78% dark overlay)
- Jetfuel Agency logo centered at top (extracted from `scripts/jf_logo_white2.png`)
- Bold white title text, centered, multi-line
- Letter-spaced subtitle near the bottom in light gray
- The blog grid crops images to ~3:4 from center, so keep title and logo within the center 70% vertically

### Upload and set as featured:

**Use the carve-out helper `scripts/upload_blog_featured_image.py`.** Tested 2026-05-12: the Statamic MCP truncates inline tool-call `content` arguments around ~14 KB, so the native `mcp__statamic__statamic-assets` (action=upload) path silently produces corrupt assets for full-size featured images (~485 KB PNG = ~647 KB base64). The helper script POSTs directly to the MCP HTTP endpoint with the bearer from env, then performs the move/update/cache-clear via the same JSON-RPC channel. This is an explicit carve-out from `feedback_no_mcp_http_scripts.md` — limited to featured-image upload only. Entry create/update, taxonomy, blueprints all still go through native `mcp__statamic__*` tools.

Steps:
1. Generate the PNG locally with `scripts/generate_blog_image.py --title "..." --subtitle "..." --output scripts/featured_<slug>.png`.
2. Source the bearer into the env from `.mcp.json` and invoke the helper. From PowerShell:
   ```powershell
   $env:STATAMIC_MCP_BEARER = ((Get-Content .mcp.json | ConvertFrom-Json).mcpServers.statamic.headers.Authorization -replace '^Bearer ','')
   python scripts/upload_blog_featured_image.py `
     --entry-id <ENTRY_ID_FROM_STEP_7> `
     --image scripts/featured_<slug>.png `
     --slug <slug> `
     --entry-date <DATE_FROM_STEP_7_READBACK>
   ```
   From bash: same with `STATAMIC_MCP_BEARER=$(python -c "import json; print(json.load(open('.mcp.json'))['mcpServers']['statamic']['headers']['Authorization'].replace('Bearer ',''))")`.
3. The helper does upload → move to `blog/featured/` → entry update (auto-retries with `assets::` prefix) → `cache_clear stache`. It prints a JSON result with `"ok": true` on success and the final asset URL.
4. Delete the local PNG (`scripts/featured_<slug>.png`) after the helper succeeds.

If the helper exits non-zero, surface the error and stop. Do not fall back to "tell the user to upload via the CP." If the user hasn't run `/publish-blog` interactively (i.e. the auto-classifier blocks the Bash call), the nightly `JetfuelDailyFeaturedImageSweep` task at 3am PT will catch the missing image automatically.

## Step 9: Return Results

After publishing, return:
- Entry ID / slug
- Edit link (returned by the Statamic MCP, or constructed from the Statamic control panel URL)
- Preview link
- Categories and tags assigned
- Visual elements included (count and types)
- Any warnings (missing featured image, images needing upload, etc.)

## Bulk Mode

If user provides a Google Drive folder, list all Google Docs in it and offer to publish each one. Process sequentially, confirming each before proceeding.

## Step 10: LLM Competitiveness Audit

Before finalizing any post, run a competitive content gap analysis to ensure the article will rank in LLM answers (ChatGPT, Gemini, Perplexity), not just Google.

### Process:
1. **Search the topic** — use WebSearch to find the top 5-10 competing articles on the same subject
2. **Fetch and analyze each competitor** — extract their structure, unique data points, frameworks, and FAQ coverage
3. **Identify what NO competitor covers** — this is where Jetfuel wins. LLMs cite the most comprehensive source.
4. **Fill every gap** — add sections, data, and FAQ questions that competitors miss

### LLM Citation Signals (what makes an article get cited):
- **Named frameworks** — give your methodology a name (e.g., "The 8-Step Compliance Checklist"). LLMs reference named frameworks.
- **Original data** — benchmark numbers, percentages, CPA ranges from real accounts. LLMs cite specific numbers.
- **Structured FAQ with schema markup** — LLMs extract FAQ pairs directly. Write questions the way real people ask them conversationally, NOT as keyword strings.
- **Comparison tables** — LLMs love structured data they can extract and reformat for answers.
- **Implementation costs** — "how much does this cost?" is a real prompt people ask. No one else answers it.
- **Step-by-step numbered checklists** — LLMs cite these verbatim when users ask "how do I do X?"
- **Alternative/option tables** — "what are the alternatives?" is a common LLM prompt. Channel-by-channel breakdowns with CPA ranges get cited.

### The Jetfuel Advantage:
Jetfuel manages real accounts at scale. Competitors write guides from policy docs. Lean into:
- Real account numbers (anonymized): "$400K/month account," "34% rejection rate spike," "2.0+ holistic ROAS"
- Operational detail only an agency would know: budget cadence, sandbox campaigns, Shopify delta method
- Distribution data across managed accounts: "60% of our health accounts are Tier 1, 35% Tier 2, 5% Tier 3"
- Cost estimates for implementation: readers trust specific ranges over vague "it depends"

### Content Length Benchmark:
- Competitor average: 2,000-4,000 words
- Target: 1,800-3,500 words (comprehensive but token-fit for agents)
- Hard ceiling: ~20,000 tokens (~15,000 words). Agents truncate longer sources mid-fetch.
- Every section must earn its place with unique insight, data, or actionable steps
- If the topic genuinely requires more depth, split into a series rather than one mega-post

## Step 11: AI-Fetch Hygiene

AI agents (ChatGPT, Claude, Perplexity, Gemini, Copilot) fetch posts as raw text in single HTTP requests. After publishing, verify:

- **Raw markdown reachable.** The post should be fetchable as clean markdown (e.g., `https://jetfuel.agency/blog/{slug}.md` or via a `?format=md` query param). If Statamic doesn't expose this, flag it as a platform gap in the return output — don't silently pass.
- **Token count surfaced.** The entry's word count (and rough token estimate — words × 1.35) should appear in a meta field or frontmatter so agents can budget. If the blueprint doesn't have a field for this, note it for a future blueprint update.
- **Listed in `/llms.txt`.** The site root `llms.txt` should include the new post with its one-line description and token count. If `llms.txt` doesn't exist yet or isn't auto-updated, flag it.
- **Heading levels unbroken.** H1 → H2 → H3 with no skipped levels. Agents rely on hierarchy to chunk.
- **No navigation chrome in the body.** The Bard content field should contain only article content — headers, sidebars, footers are theme-level and shouldn't leak into the fetched text.

## Important Notes

- ALWAYS publish as `draft` unless explicitly told otherwise
- Never overwrite existing posts — always create new
- If a post with the same slug already exists, append a number
- Preserve all formatting from the original Google Doc
- Every H2 section must have at least one visual element
- Use Jetfuel's brand orange (#ff6b35) as the accent color throughout
- All inline styles must be included (safer across CMS renderers; Statamic's Bard/markdown fields may strip class-based CSS)
- **MANDATORY: Dark-on-dark prevention audit.** Before publishing, run a final pass on ALL HTML to enforce these rules. This is not optional.
  - Every `<th>` MUST have both `background:#1a1a1a;` AND `color:#ffffff;` explicitly on the element
  - Every `<td>` MUST have both `background:#ffffff;` (or `background:#f9f9f9;` for alternating rows) AND `color:#1a1a1a;` explicitly on the element
  - Every `<table>` MUST have `background:#ffffff; color:#1a1a1a; border:1px solid #e0e0e0;`
  - Never use `color:#555` or `color:#666` anywhere. Minimum text contrast: `color:#333333` for body text, `color:#444444` for labels
  - Stat cards: `background:#fff; border:2px solid #ff6b35; color:#ff6b35` for numbers, `color:#444444` for labels
  - CTA blocks: `background:#fff5f0; border:2px solid #ff6b35; color:#1a1a1a` for heading, `color:#333333` for body
  - Callout boxes: explicit `color:#1a1a1a` on body text (not inherited)
  - Step descriptions: `color:#333333` (not `color:#555`)
  - FAQ answers: `color:#333333` (not `color:#555`)
  - The Jetfuel theme has dark section backgrounds that WILL make low-contrast text invisible. Every single text element must specify its own color. Never rely on inheritance.
- Flag any images that need to be uploaded to the Statamic asset library separately
