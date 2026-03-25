# Marketing Skills for Claude Code

AI-powered marketing automation skills built for [Claude Code](https://claude.com/claude-code).

## Skills

### `/publish-blog`
Publish Google Docs as WordPress blog posts with:
- Rich media (stat cards, comparison tables, progress bars, callout boxes, step-by-step visualizations)
- Table of contents with anchor links
- Key takeaways box
- FAQ section with schema markup
- Auto-generated featured images matching your blog's template
- SEO metadata (categories, tags, excerpt)
- Publishes as draft by default

**Setup:**
1. Copy `publish-blog/` to `.claude/ops/publish-blog/`
2. Copy `publish-blog/command.md` to `.claude/commands/publish-blog.md`
3. Copy `scripts/` to your project's `scripts/` directory
4. Add your WordPress app password to `.claude/me.json`:
   ```json
   { "wordpress": { "app_password": "your-app-password" } }
   ```
5. Update `publish-blog/config.json` with your site URL, categories, and author ID

**Dependencies:**
```bash
pip install Pillow requests
```

**Usage:**
```
/publish-blog https://docs.google.com/document/d/your-doc-id/edit
```

## Featured Image Generator

Standalone script to generate blog featured images:

```bash
python3 scripts/generate_blog_image.py \
  --title "Your Post Title" \
  --subtitle "Optional subtitle" \
  --output featured.png
```

Customize by replacing `scripts/stock_bg.jpg` with your own background photo and `scripts/jf_logo_white2.png` with your logo.

## License

MIT
