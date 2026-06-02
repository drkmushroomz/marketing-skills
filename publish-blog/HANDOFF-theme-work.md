# Agentic Engine Optimization — Theme-Level Handoff

These items can't be done via the Statamic MCP. They need a PR against the jetfuel.agency Statamic theme repo. Scope is small; group them into one ticket.

## 1. Serve `/llms.txt` at the site root

**File:** generated at `jetfuel-crew/scripts/llms.txt`. Copy into the theme's `public/` (or equivalent static-asset path), or expose via an Antlers route that returns it with `Content-Type: text/plain; charset=utf-8`.

**Refresh:** regenerate when blog inventory changes meaningfully. A lightweight follow-up would be a Statamic addon/command that rebuilds `llms.txt` on entry save — but a manual regenerate from the `publish-blog` skill every month is fine for v1.

**Spec reference:** <https://llmstxt.org/>.

## 2. Clean-markdown endpoint per entry

**Goal:** `GET /{slug}.md` returns the post body as markdown with a minimal frontmatter header (title, published date, token count, canonical URL). No navigation, no sidebar, no footer. `Content-Type: text/markdown; charset=utf-8`.

**Why:** AI agents fetch pages into 100–200K token contexts. HTML with nav chrome wastes tokens and parses poorly. A dedicated `.md` endpoint cuts their payload by ~60% and makes extraction deterministic.

**Approach:** Antlers route pattern `{slug}.md` → template that serializes the Bard content field through a markdown renderer and strips layout chrome. Statamic's `{{ content | raw }}` is close but needs a Bard-to-markdown pass; one option is the community `statamic/markdown` field tag or a small custom serializer.

**Acceptance:**
- `curl https://jetfuel.agency/ai-vs-human-marketers-2026.md` returns clean markdown.
- Token count in frontmatter matches `content.length / 4` approximately.
- No HTML tags in output other than what markdown explicitly permits (code blocks, etc.).

## 3. "Copy as markdown" button on blog post template

**UI:** small button in the post header (next to share icons). Label: "Copy for AI". On click, fetches `{slug}.md` and writes to clipboard with a toast confirmation.

**Why:** makes it trivial for readers to paste a full post into ChatGPT/Claude/Perplexity. Every click is a potential citation. Also serves as the canonical way for Edwin to hand pieces to agents during research.

**Acceptance:** button visible on every blog entry; copies clean markdown; works in Safari, Chrome, Firefox (clipboard API).

## 4. (Optional v2) Token count in entry meta

Add a `token_count` field to the `blog_post` blueprint and populate on save (word count × 1.35 is a good estimate). Surface in the `.md` endpoint's frontmatter and in `llms.txt` regeneration. Not blocking.
