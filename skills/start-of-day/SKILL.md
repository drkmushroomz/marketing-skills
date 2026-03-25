---
name: start-of-day
description: Morning briefing — email digest, Slack catch-up, and calendar for the day
disable-model-invocation: true
---

# Start of Day

Morning briefing that catches you up on email, Slack, and your calendar for the day.

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user identity (name, email, Slack User ID, timezone). If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for preferences under `skills.start-of-day.preferences`:
     - `morning_order` — `"email-slack-calendar"` (default), `"slack-email-calendar"`, or `"calendar-email-slack"`
     - `include_clickup` — whether to pull ClickUp tasks (default: false)
   - Read `skills._shared` for `role_context` and `team_members`.

2. **Greet briefly:**
   - "Good morning, {first name}. Here's your {day of week}."

3. **Run sections in the user's preferred `morning_order`:**

   Execute each section below in the order specified by `morning_order`. Each section is self-contained.

   ---

   ### EMAIL section
   Run the full email update workflow:
   - Read `.claude/ops/daily-email-update/PROMPT.md` and `.claude/ops/daily-email-update/rules.md`
   - Read `.claude/ops/daily-email-update/config.json` for team defaults
   - Determine time window from `.claude/ops/daily-email-update/state.json` (or default to yesterday 8 AM)
   - Build Gmail search query from config layers
   - Execute the full retrieval → classification → digest pipeline per PROMPT.md
   - Send digest email to user
   - Update state.json
   - Display summary inline: count of Needs Response + Needs Action items

   ---

   ### SLACK section
   Catch up on Slack:
   - Use preferences from `skills.slack-summary.preferences` (priority_channels, ignore_channels, include_dms)
   - Time window: since yesterday evening (or last start-of-day run)
   - Fetch channel activity, filter out ignored channels, prioritize priority channels
   - For each active channel, summarize: action items first, then key updates
   - Include DMs if enabled
   - Display inline summary

   ---

   ### CALENDAR section
   Review today's schedule:
   - Use Google Calendar to list today's events in user's timezone
   - Show each event: time, title, attendees, location/link
   - Flag meetings starting in the next 2 hours
   - Note any gaps or back-to-back blocks
   - If meetings have attached docs or agendas (Drive links), mention them

   ---

4. **ClickUp tasks (if enabled):**
   - If `include_clickup` is true:
     - Fetch tasks assigned to the user that are due today or overdue
     - Show: task name, list, due date, priority
     - Flag overdue items

5. **Wrap up:**
   Display a quick summary:
   ```
   TODAY AT A GLANCE
   =================
   {n} emails need attention | {n} Slack action items | {n} meetings | {n} tasks due

   First meeting: {time} — {name}
   Top priority: {most urgent item from email/slack/tasks}
   ```

## Notes
- Display all times in user's timezone from me.md
- Each section should be clearly separated with a heading
- If any service fails (e.g., Slack token expired), report the error and continue with remaining sections — don't halt the whole briefing
- Statement tone, concise, summaries at the top
- The email section follows ALL rules from PROMPT.md and rules.md — do not simplify or skip steps
