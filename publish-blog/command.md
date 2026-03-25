Publish a Google Doc as a draft blog post on jetfuel.agency.

Read the skill prompt at `.claude/ops/publish-blog/PROMPT.md` and config at `.claude/ops/publish-blog/config.json`.

Steps:
1. Read the Google Doc content via `get_doc_as_markdown` (use edwin@jetfuel.agency)
2. Extract title from H1, body as HTML, meta description from first paragraph or explicit "Meta:" line
3. Map to WordPress categories using config.json category list
4. Publish as DRAFT via `scripts/wp_publish.py`. Read the WP app password from `.claude/me.json` under `wordpress.app_password`
5. Return the edit link and preview link

Always publish as draft. Never publish live without explicit confirmation.

$ARGUMENTS
