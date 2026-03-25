---
name: daily-recap
description: End-of-day summary — what you accomplished, meetings, communications, and carry-forward items
disable-model-invocation: true
---

# Daily Recap

End-of-day summary of what happened today.

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user identity (name, email, Slack User ID, timezone). If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for preferences under `skills.daily-recap.preferences`:
     - `detail_level` — `"concise"` (default) or `"detailed"`
     - `include_dev_activity` — whether to include git commits (default: false)
     - `focus_areas` — what to organize the recap around
   - Read `skills._shared.role_context` for relevance weighting.

2. **Gather today's calendar:**
   - Use Google Calendar to list today's events.
   - Note meetings attended, who was there, and duration.
   - If `detail_level` is `"detailed"`, check for Google Meet transcripts in Drive (if `skills.fetch-daily-transcripts.preferences.use_google_transcripts` is true).

3. **Gather today's email activity:**
   - Read `.claude/ops/daily-email-update/state.json` for today's email digest stats if available.
   - If the email update ran today, summarize: how many needed response, how many needed action.
   - Check for any emails sent by the user today (replies, new threads).

4. **Gather today's Slack activity:**
   - Use Slack `conversations_search_messages` to find messages the user sent or was mentioned in today.
   - Summarize key conversations and decisions.

5. **Gather ClickUp activity (if enabled):**
   - If `skills.start-of-day.preferences.include_clickup` is true:
     - Check for tasks completed, updated, or commented on today.

6. **Gather dev activity (if enabled):**
   - If `include_dev_activity` is true:
     - Scan git repos for today's commits by the user.
     - If `skills.dev-activity.preferences.include_repos` is `"all"`, scan `~/Projects/`.
     - If specific repos listed, scan only those.
     - Exclude repos in `exclude_repos`.
     - Summarize: commits, PRs opened/merged, code review activity.

7. **Compose the recap:**
   - Organize by `focus_areas` if set, otherwise by activity type.
   - For `"concise"`: bullet points, highlights only.
   - For `"detailed"`: fuller context, meeting notes, follow-up items.

8. **Output format:**

### Concise format:
```
DAILY RECAP — {date}
====================

ACCOMPLISHED
- {what you did, organized by focus_areas}
- {key decisions made}

MEETINGS ({n} today)
- {time} · {meeting name} — {key outcome or decision}

COMMUNICATIONS
- {n} emails needed response, {n} needed action
- Key Slack threads: {brief summary}

CARRY FORWARD
- {items that need follow-up tomorrow}
```

### Detailed format:
Same structure but with:
- Meeting notes and attendee lists
- Full email thread summaries for items actioned
- Slack conversation context
- Git commit summaries (if enabled)
- Explicit next steps per item

## Notes
- Display all times in user's timezone from me.md
- Focus on what the USER did and decided, not what happened around them
- Carry Forward section is critical — surface anything unresolved
- Statement tone, no hedging
- If it was a light day, keep it short — don't pad
