---
name: slack-summary
description: Slack catch-up — summarizes channel activity, DMs, and action items
disable-model-invocation: true
---

# Slack Summary

Catch up on what happened in Slack since your last check.

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user identity (name, email, Slack User ID, timezone). If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for user preferences under `skills.slack-summary.preferences`:
     - `priority_channels` — show these first
     - `ignore_channels` — skip these entirely
     - `include_dms` — whether to include DMs (default: true)
   - Read `skills._shared.role_context` to determine relevance weighting.
   - Read `skills._shared.team_members` to identify colleague activity.

2. **Determine the time window:**
   - Default: last 12 hours. If $ARGUMENTS contains a time range (e.g., "since yesterday", "last 24h"), use that instead.

3. **Fetch channel list:**
   - Use Slack `channels_list` to get all channels the user is a member of.
   - Filter out any channels in `ignore_channels`.
   - Sort: `priority_channels` first, then remaining channels alphabetically.

4. **Fetch messages per channel:**
   - Use `conversations_history` for each channel within the time window.
   - Skip channels with no messages in the window.
   - For threads with 3+ replies, use `conversations_replies` to get full context.
   - Rate limiting: if throttled, wait 3 seconds and retry. Max 3 retries per channel.

5. **Fetch DMs (if enabled):**
   - Use `conversations_search_messages` to find DMs mentioning or sent to the user.
   - Include unread DMs from the time window.

6. **Classify and summarize:**
   For each channel with activity, produce a summary:
   - **Action needed**: Messages where the user is @mentioned, asked a question, or assigned something.
   - **Key updates**: Important decisions, announcements, or status changes relevant to user's role.
   - **Conversation highlights**: Active discussions the user should be aware of.
   - Skip: casual chat, emoji reactions only, bot messages with no actionable content.

7. **Output format:**

```
SLACK SUMMARY — {date}
======================

{n} channels active | {n} action items | Window: {start} → {end}

ACTION NEEDED
-------------
• #{channel} · @{person} — {what they need from you}
• DM · {person} — {what they asked}

PRIORITY CHANNELS
-----------------
### #{channel-name}
- {summary of key discussion or decision}
- {thread}: {brief context} ({n} replies)

OTHER CHANNELS
--------------
### #{channel-name}
- {summary}
```

## Notes
- Display all times in user's timezone from me.md
- Bias toward including items where the user is mentioned or their role is relevant
- If a team member from `team_members` is already handling something, note it but deprioritize
- Statement tone, concise — one line per item unless thread context is needed
- If no activity in any channel, say so: "Quiet day — nothing requiring your attention."
