# connect

## Description
First-run command to verify all MCP connections and set up user preferences. Run this once after setup.sh.

## Process
1. Read `.claude/me.md` to confirm identity is set up. If missing, tell the user to run `./setup.sh` first and stop.

2. **Test Slack**: Use the Slack MCP tool to search for a recent message. If it fails, tell the user their Slack token may be invalid and to re-run `./setup.sh`.

3. **Test Google Workspace**: Use the Google Workspace MCP tool to list calendars or search Gmail. This will trigger the first-time OAuth flow — a browser window will open asking the user to sign in with their @jetfuel.agency Google account. Walk them through it:
   - "A browser window should open asking you to sign in to Google."
   - "Sign in with your @jetfuel.agency account and click Allow."
   - If it works: confirm "Google Workspace connected!"
   - If it fails: provide troubleshooting steps

4. **Set up Gmail preferences** (only if Google Workspace connected):
   a. Load `.claude/me.json` if it exists, otherwise start with empty `{}`
   b. Determine Gmail auth param:
      - Ask: "When you open Gmail in your browser, does the URL show `/u/0/`, `/u/1/`, or something else? (Check the address bar — it's the number after /u/)"
      - Save to `gmail.auth_param` in me.json (default: `/u/0/`)
   c. Show the default email search query from `config.json` (`gmail_search_query.org_exclusions` + `gmail_search_query.noise_exclusions`)
      - Tell the user: "This is the default filter that removes noise from your email digest. Copy it into Gmail search to test — you should see only emails that matter to you."
      - Show the full query string
      - Ask: "Want to add any personal exclusions? For example: `-from:somevendor@example.com` or `-label:my-noise-label`. You can always update this later in `.claude/me.json`."
      - If they provide exclusions, save to `gmail.search_exclusions` in me.json
   d. Write the final `.claude/me.json`

5. **Test ClickUp**: Use a ClickUp MCP tool (like searching workspace). This may also trigger a browser OAuth flow. Walk them through it similarly.

6. **Test Jetfuel HQ**: Use the `hq_get_my_profile` tool to verify the HQ connection. If it works, confirm with the user's name and roles. If it fails (401/403), tell them to re-run `./setup.sh` to re-authenticate.

7. **Skill Personalization**: After all connections are verified, walk the user through personalizing their tools.

   Display introduction:
   > **Let's personalize your tools.** I'm going to ask you a few quick questions so your daily briefings, email digests, and Slack summaries are tailored to YOUR role — not one-size-fits-all. This takes about 2 minutes.
   >
   > You can skip any question (I'll use sensible defaults) and change answers anytime by saying "reset my preferences."

   Use `AskUserQuestion` for each question below. If the user skips or says "I don't know", use the listed default and say "No problem, you can change this anytime."

   Save all answers to `.claude/me.json` under a `skills` key. Set `skills.<slug>.onboarded = true` for each completed section.

   ---

   **Shared (applies across all skills) → `skills._shared`**

   **Q1 — Role** (`skills._shared.role_context`, default: `"General team member"`):
   > "What do you do at Jetfuel? Just a sentence or two is fine.
   > This helps me understand which emails and messages are actually important to you vs. just FYI."
   >
   > *Examples: "I'm an account manager — I talk to clients and coordinate the team", "I do paid media — mostly Facebook and Google ads", "I handle operations and finance"*

   **Q2 — Team** (`skills._shared.team_members`, default: `[]`):
   > "Who do you work with most? Just first names.
   > When I see them already handling something (like replying to a client), I won't bug you about it."
   >
   > *Examples: "Kim, Edwin, Mel" or "mostly the dev team"*

   ---

   **Email Update → `skills.email-update.preferences`**

   **Q3 — Topics** (`priority_topics`, default: `[]`):
   > "What are your top priorities right now? Projects, clients, anything.
   > I'll make sure emails about these get flagged so they don't get buried."
   >
   > *Examples: "Barker Wellness launch", "recruiting", "SOW reviews"*

   **Q4 — Financial emails** (`financial_emails`, default: `"skip"`):
   > "Do you handle finances — like approving invoices or reviewing budgets?
   > Most people are just CC'd on those and don't need to see them. But if you approve them, I should flag them."
   >
   > - **No** (default) — skip financial/accounting emails
   > - **Yes** — flag them as Needs Action

   **Q5 — Noise** (`skip_domains`, default: `[]`; also append to `gmail.search_exclusions`):
   > "Any emails you always delete without reading? Like a vendor newsletter or automated notifications.
   > Give me the sender name or domain and I'll filter them out. You can always add more later."

   ---

   **Slack Summary → `skills.slack-summary.preferences`**

   **Q6 — Priority channels** (`priority_channels`, default: `[]`):
   > "Which Slack channels are most important to you?
   > I'll highlight what happened there first so you see it before the noise."
   >
   > *Examples: "#client-updates", "#team-requests", or "any channel with my clients' names"*

   **Q7 — Skip channels** (`ignore_channels`, default: `[]`):
   > "Any channels you don't need updates from? Like #random or #social.
   > I'll leave those out of your summaries."

   **Q8 — DMs** (`include_dms`, default: `true`):
   > "Should I include your DMs in Slack summaries? Some people find it useful, others prefer to check DMs themselves."
   >
   > - **Yes** (default) — include DMs
   > - **No** — skip DMs

   ---

   **Daily Recap → `skills.daily-recap.preferences`**

   **Q9 — Detail level** (`detail_level`, default: `"concise"`):
   > "At the end of the day, I can write up what you accomplished. Do you prefer:
   > - **Concise** (default) — quick bullet points, just the highlights
   > - **Detailed** — fuller context, meeting notes, follow-up items"

   **Q10 — Focus** (`focus_areas`, default: `[]`):
   > "What should your recap focus on? This helps me organize what matters most at the top."
   >
   > *Examples: "client deliverables", "team management", "ad campaigns", "internal projects"*

   ---

   **Start of Day → `skills.start-of-day.preferences`**

   **Q12 — Morning order** (`morning_order`, default: `"email-slack-calendar"`):
   > "When you start your day, what do you want to see first?
   > - **Email then Slack** (default) — email digest first, then Slack catch-up, then calendar
   > - **Slack then Email** — Slack first
   > - **Calendar first** — today's meetings first, then email and Slack"

   **Q13 — ClickUp** (`include_clickup`, default: `false`):
   > "Do you use ClickUp? If so, I'll pull in your tasks for the day."
   >
   > - **Yes** — include ClickUp tasks
   > - **No** (default) — skip ClickUp

   ---

   **Meeting Transcripts → `skills.fetch-daily-transcripts.preferences`**

   **Q14 — Google Meet** (`use_google_transcripts`, default: `true`):
   > "Do your meetings use Google Meet? I can pull transcripts from Google Drive."
   >
   > - **Yes** (default) — pull Google Meet transcripts
   > - **No** — skip Google transcripts

   ---

   After all questions, set `skills.<slug>.onboarded = true` for each section: `_shared`, `email-update`, `slack-summary`, `fetch-daily-transcripts`.

   Write the final `.claude/me.json` with all preferences.

   Display wrap-up:
   > All set! Your tools are personalized. Here's what you can do:
   >
   > - `/start-of-day` — morning briefing (email + Slack + calendar)
   > - `/email-update` — email digest anytime
   > - `/slack-summary` — what happened in Slack
   > - `/daily-recap` — end-of-day summary
   >
   > To change your preferences anytime, just say "reset my preferences for [skill name]."

8. **Summary**: Print connection status and settings status.

## me.json Structure
```json
{
  "gmail": {
    "auth_param": "/u/0/",
    "search_exclusions": "-from:somevendor@example.com"
  },
  "skills": {
    "_shared": {
      "onboarded": true,
      "role_context": "Account manager — I handle client comms",
      "team_members": ["Kim", "Edwin"]
    },
    "email-update": {
      "onboarded": true,
      "preferences": {
        "priority_topics": ["client onboarding", "SOW approvals"],
        "financial_emails": "skip",
        "skip_domains": ["marketing-tool.com"]
      }
    },
    "slack-summary": {
      "onboarded": true,
      "preferences": {
        "priority_channels": ["#client-updates"],
        "ignore_channels": ["#random"],
        "include_dms": true
      }
    },
    "daily-recap": {
      "onboarded": true,
      "preferences": {
        "detail_level": "concise",
        "focus_areas": ["client deliverables"]
      }
    },
    "start-of-day": {
      "onboarded": true,
      "preferences": {
        "morning_order": "email-slack-calendar",
        "include_clickup": false
      }
    },
    "fetch-daily-transcripts": {
      "onboarded": true,
      "preferences": {
        "use_google_transcripts": true
      }
    }
  }
}
```

Skills read this file for user-specific settings, falling back to `.claude/ops/daily-email-update/config.json` for team defaults.

## Output
```
Connection Status:
✓ Identity: [Name] ([email])
✓ Slack: Connected as @[username]
✓ Google Workspace: Connected ([email])
  ✓ Preferences saved to .claude/me.json
✓ ClickUp: Connected
✓ Jetfuel HQ: Connected as [name] ([roles])
✓ Skills personalized (X/Y questions answered)
```

If any service fails, provide clear next steps to fix it.

## Re-onboarding
If a user says "reset my preferences for [skill]":
1. Set `skills.<slug>.onboarded = false` in me.json
2. Clear `skills.<slug>.preferences`
3. Re-run that skill's questions from the questionnaire above
4. Set `onboarded = true` when complete
