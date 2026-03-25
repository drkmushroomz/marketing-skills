---
name: share
description: Share the current Claude Code conversation to Jetfuel HQ for team review
disable-model-invocation: true
---

Share the current Claude Code conversation to Jetfuel HQ for team review.

## Steps

1. **Find the current session JSONL file:**
   - Session files live in `~/.claude/projects/{encoded-project-dir}/`
   - The encoded project dir replaces `/` with `-` in the working directory path
   - List `.jsonl` files in that directory sorted by modification time and pick the most recent one
   - Example: if working dir is `/Users/chris/Projects/jetfuel-hq`, check `~/.claude/projects/-Users-chris-Projects-jetfuel-hq/`

2. **Run the share script:**
   ```bash
   jf-share <path-to-session.jsonl> --visibility=unlisted
   ```
   If `jf-share` is not found, fall back to:
   ```bash
   node "$(find ~ -path '*/jetfuel-crew/scripts/share.js' -maxdepth 4 2>/dev/null | head -1)" <path-to-session.jsonl> --visibility=unlisted
   ```

3. **Display the result:**
   - Show the shareable URL returned by the script
   - Mention the message count and any redactions applied

## Notes
- The script auto-redacts API keys, tokens, and secrets before uploading
- Default visibility is `unlisted` (accessible via URL but not listed publicly)
- To make it public or private, add `--visibility=public` or `--visibility=private`
- If the upload fails due to auth, remind the user to check their `HQ_API_TOKEN` in the crew `.env`
- View all your shared conversations at `https://hq.jetfuel.agency/s`
