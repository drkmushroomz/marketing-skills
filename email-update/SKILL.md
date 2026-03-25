---
name: email-update
description: Email triage digest — classifies emails and sends a summary of what needs your attention
disable-model-invocation: true
---

# Email Update

Run the daily email triage workflow defined in `.claude/ops/daily-email-update/PROMPT.md`.

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user identity (name, email, timezone). If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for user-specific overrides.
   - Read `.claude/ops/daily-email-update/config.json` for team defaults.
   - For each setting, use me.json value if present, otherwise config.json value.

2. **Load the workflow prompt:**
   - Read `.claude/ops/daily-email-update/PROMPT.md` in full.
   - Read `.claude/ops/daily-email-update/rules.md` for classification rules.

3. **Determine the time window:**
   - Read `.claude/ops/daily-email-update/state.json` if it exists for the last checkpoint.
   - If no state file, default to yesterday at 8:00 AM in the user's timezone.

4. **Execute the workflow exactly as PROMPT.md specifies:**
   - Build the Gmail search query from config layers (org exclusions + noise exclusions + user exclusions + skip domains).
   - Phase 1: Capture all message IDs → `expected_count`
   - Phase 2: Batch retrieve content (batches of 10, 3-sec delays between batches, 10-sec wait on 429 errors)
   - Phase 3: Mandatory retry for any failed retrievals (batches of 5, 5-sec delays, up to 3 retries per ID)
   - Phase 4: HALT if `retrieved_count < expected_count` after all retries
   - Classify each email per rules.md
   - Apply user preference modifiers (role_context, team_members, priority_topics, financial_emails)

5. **Send the digest:**
   - Format per PROMPT.md output format (plain text, no FYI section, no drafts)
   - Send ONLY to the user's email from me.md
   - Include Gmail links using the user's `gmail.auth_param`

6. **Update state:**
   - Write `.claude/ops/daily-email-update/state.json` with run metadata

## Notes
- Never proceed with incomplete email retrieval
- Never create draft emails — send the digest directly
- When uncertain about classification, flag it (bias toward Needs Response)
- Preserve unread status for emails user hasn't opened
- Display all times in user's timezone
