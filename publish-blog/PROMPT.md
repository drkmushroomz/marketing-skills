# Publish Blog Post to WordPress

<role>
You publish blog content from Google Docs to jetfuel.agency as WordPress draft posts — with rich media, infographic-style visualizations, and a strong editorial structure.
</role>

<task>
Given a Google Doc (URL, ID, or name), read the content, transform it to a premium WordPress blog post with embedded rich media, custom visual elements, and a table-of-contents-driven structure, then publish as a draft via the WordPress REST API.
</task>

## Setup

1. Read config from `.claude/ops/publish-blog/config.json`
2. WordPress app password from `.claude/me.json` under `wordpress.app_password`
3. Google Docs access via `edwin@jetfuel.agency`

## Step 1: Read the Google Doc

Use `get_doc_as_markdown` MCP tool to pull the document content. If user provides a URL, extract the doc ID from it.

## Step 2: Build the Post Structure

Every post follows this editorial template (inspired by Single Grain's long-form structure):

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

For every major section (H2), include at least ONE visual element. Choose the best format based on content:

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

For external content, use WordPress embed blocks:
- **YouTube**: `<figure class="wp-block-embed is-type-video"><div class="wp-block-embed__wrapper"><iframe src="https://www.youtube.com/embed/VIDEO_ID" width="100%" height="400" frameborder="0" allowfullscreen></iframe></div></figure>`
- **Twitter/X**: Use the tweet URL in a WordPress embed block
- **Images**: `<figure class="wp-block-image size-large"><img src="URL" alt="descriptive alt text" /><figcaption>Caption text</figcaption></figure>`
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

**Minimum requirement: at least 3 visual elements per 1,500-word post.**

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

## Step 7: Publish via WordPress REST API

Use `scripts/wp_publish.py` with the app password from `.claude/me.json`:

```bash
python3 scripts/wp_publish.py \
  --title "Post Title" \
  --content-file content.html \
  --slug "post-slug" \
  --categories "68,155" \
  --tags "ecommerce,food-beverage" \
  --excerpt "Meta description here" \
  --status draft \
  --author 1 \
  --password "from me.json"
```

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
```python
import requests, base64

creds = base64.b64encode(b'edwin:<app_password>').decode()

# Upload to media library
with open('scripts/featured_image.png', 'rb') as f:
    resp = requests.post('https://jetfuel.agency/wp-json/wp/v2/media',
        headers={'Authorization': f'Basic {creds}',
                 'Content-Disposition': 'attachment; filename="slug-name-cover.png"',
                 'Content-Type': 'image/png'},
        data=f.read())
media_id = resp.json()['id']

# Set on post
requests.post(f'https://jetfuel.agency/wp-json/wp/v2/posts/{post_id}',
    headers={'Authorization': f'Basic {creds}', 'Content-Type': 'application/json'},
    json={'featured_media': media_id})
```

## Step 9: Return Results

After publishing, return:
- Post ID
- Edit link: `https://jetfuel.agency/wp-admin/post.php?post={id}&action=edit`
- Preview link
- Categories and tags assigned
- Visual elements included (count and types)
- Any warnings (missing featured image, images needing upload, etc.)

## Bulk Mode

If user provides a Google Drive folder, list all Google Docs in it and offer to publish each one. Process sequentially, confirming each before proceeding.

## Important Notes

- ALWAYS publish as `draft` unless explicitly told otherwise
- Never overwrite existing posts — always create new
- If a post with the same slug already exists, append a number
- Preserve all formatting from the original Google Doc
- Every H2 section must have at least one visual element
- Use Jetfuel's brand orange (#ff6b35) as the accent color throughout
- All inline styles must be included (WordPress strips external CSS classes)
- **Dark-on-dark prevention**: The blog theme can have dark section backgrounds. Every `<table>`, `<tr>`, and `<td>` MUST have explicit `background` and `color` inline styles (e.g., `background:#ffffff; color:#1a1a1a;` on the `<table>`, `color:#1a1a1a;` on every `<td>`). Never rely on inherited text/background colors.
- Flag any images that need to be uploaded to WordPress media library separately
- The app password should be read from `.claude/me.json` — never hardcode it
