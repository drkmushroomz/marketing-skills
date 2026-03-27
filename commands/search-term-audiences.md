# Search Term Audiences

Analyze a brand's search landscape and build custom audience segments for Google Ads Demand Gen campaigns.

## Arguments

- `$ARGUMENTS` — account slug (e.g. `barker-wellness`), plus optional flags:
  - `--dry-run` — preview segments without creating (DEFAULT)
  - `--create` — create approved segments in Google Ads
  - `--refresh` — regenerate segments for an account that already has them
  - `--phase <N>` — start at a specific phase (1-4)

## Steps

1. **Load identity and config:**
   - Read `.claude/me.md` for user identity.
   - Read `.claude/ops/search-term-audiences/config.json` for accounts and settings.

2. **Load the workflow:**
   - Read `.claude/skills/search-term-audiences/PROMPT.md` in full.

3. **Resolve account:**
   - If `$ARGUMENTS` contains a known account slug, use it.
   - If empty or unrecognized, list available accounts and ask.

4. **Load the client brief:**
   - Read the `client_brief` path from the account config.

5. **Execute the 4-phase workflow as PROMPT.md specifies:**
   - Phase 1: Gather brand intelligence (Google Ads, Slack, Gmail, Drive, HQ)
   - Phase 2: Generate themed audience segments
   - Phase 3: Present for user review
   - Phase 4: Create in Google Ads (only with `--create` flag + user approval)

$ARGUMENTS
