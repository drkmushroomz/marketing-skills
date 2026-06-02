---
name: jetfuel-featured-images
description: Create, fix, upload, and verify jetfuel.agency blog featured images in Statamic. Use when a Jetfuel blog card image is missing, falling back to the logo, using the wrong asset, visually broken, needs a new featured image, or when updating a Statamic blog entry's featured_image/og_image asset.
---

# Jetfuel Featured Images

Use this skill for Jetfuel blog featured-image work only. The goal is to leave the public blog card using a real 1200x1200 PNG in `blog/featured/`, with the Statamic entry verified and the live HTML checked.

## Golden Rules

- Blog entries live in Statamic `blog`; do not edit stale flat files.
- Featured images belong in the `assets` container under `blog/featured/`.
- The final `featured_image` value shown by `statamic-entries get` should look like `blog/featured/<slug>-vN.png`.
- If entry update validation says the asset is missing, update with the full Statamic asset id string: `assets::blog/featured/<slug>-vN.png`. Readback should normalize to `blog/featured/<slug>-vN.png`.
- Never upload title-card images at the asset container root as the final state.
- Never use SVG title cards, 16:9 masters, logo fallbacks, old logos, or hand-made logo approximations.
- Preserve the entry's existing `date` field in every update payload.
- Do not change slugs.

## Diagnose

1. Fetch the live blog HTML or entry page and identify the affected posts.
   - If the image is `/site-images/jetfuel_full.webp`, the entry probably has no `featured_image`.
   - If the image is a one-off JPG/SVG/root asset, replace it with the current PNG card system.
2. Read each Statamic entry with `statamic-entries get` before writing. Record:
   - `id`
   - `slug`
   - `title`
   - `date`
   - current `featured_image`

## Reuse or Generate

Before generating, list assets under `blog/featured/` and local files such as `scripts/featured_*.png`, `scripts/_*_featured.png`, and `scripts/generated-featured-*`.

Reuse an existing image only when it clearly matches the exact post. Otherwise generate a new card with:

```
python scripts\generate_blog_image.py --title "<short display title>" --subtitle "<SHORT SUBTITLE>" --output "scripts\<slug>-vN.png"
```

Image requirements:

- 1200x1200 PNG master.
- Current template: `scripts/stock_bg.jpg`, dark overlay/blur, centered `scripts/jf_logo_white_current.png`, centered white title, letter-spaced subtitle near bottom.
- Shorten long SEO titles into display title plus subtitle.
- Use versioned filenames like `<slug>-v2.png` when replacing an existing or disputed path.

## Upload Without Getting Stuck

The Statamic asset MCP has two traps:

- `upload` rejects folder paths in `filename`.
- `move` treats `destination` without a trailing slash as a folder named after the file.

Use this exact sequence:

1. **Upload to root** with basename only:
   - `filename`: `<slug>-vN.png`
   - `content`: base64 PNG
   - `encoding`: `base64`
2. **Move from root into the folder**:
   - `path`: `<slug>-vN.png`
   - `destination`: `blog/featured/`
   - The trailing slash is required.
3. **Get** the asset at:
   - `path`: `blog/featured/<slug>-vN.png`
4. **Verify**:
   - `width`: 1200
   - `height`: 1200
   - `mime_type`: `image/png`

If a previous attempt created `blog/featured/<slug>.png/<slug>.png`, abandon that path and use a fresh `-vN.png` filename. Delete the bad nested asset later only if it is safe and not referenced.

## Update Entry

Update only the image field unless the user asked for more. Always preserve `date`.

Preferred payload:

```json
{
  "date": "<existing date>",
  "featured_image": "blog/featured/<slug>-vN.png"
}
```

If validation fails with `Asset [...] not found`, retry with:

```json
{
  "date": "<existing date>",
  "featured_image": "assets::blog/featured/<slug>-vN.png"
}
```

Set `og_image` only when the user explicitly wants a separate social card. Otherwise let it fall back to `featured_image`.

## Cache and Verify

After updates:

1. Clear Statamic caches:
   - `statamic-system cache_clear stache`
   - `statamic-system cache_clear all` if the page still reads stale.
   - Static cache may report disabled; that is not a blocker.
2. Read each entry again with `statamic-entries get`.
   - Confirm `featured_image` readback is the normalized `blog/featured/<slug>-vN.png`.
3. Check each R2 image URL returns `200 image/png`.
4. Fetch `https://jetfuel.agency/blog/` and inspect the top card `<img src>`.
   - Confirm the live HTML references `/images/blog/featured/<slug>-vN.png`.

If Statamic readback is correct but live HTML is stale, the static frontend has not rebuilt yet. Ask an editor/admin to trigger the Cloudflare Pages rebuild, then verify again.

## Cleanup

Remove local throwaway generated images after upload unless they are intentionally being kept as reusable masters. Ignore unrelated dirty git files.

Delete temporary test assets from Statamic if they were created during debugging and are clearly unreferenced. Do not delete old production images unless the user asked for asset cleanup.
