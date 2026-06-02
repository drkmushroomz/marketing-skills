# Rules

## Classifications (choose one per thread)

### Needs Response
**Criteria**: User must reply personally
- User is in TO: line (not CC/BCC) AND email body content is directed to user (not just on TO line), OR
- User is explicitly called out by name in the email content
- Someone else in thread has NOT already handled the request
- Exclude if it's just an FYI where user is copied on group communications
- **Financial/Accounting Emails**: Only classify as Needs Response if user's name is specifically mentioned in email body content

**HIGH PRIORITY - Direct 1:1 Threads**:
- If user is the ONLY recipient (sole TO:, no CC) in an established back-and-forth thread → Always flag as Needs Response
- These threads indicate direct relationship where user is the primary/only point of contact
- Examples: Recruiting candidates, vendor contacts, external consultants, direct client relationships
- **Processing requirement**: Always pull full thread content for 1:1 threads, never rely on metadata/subject alone

**Follow-up After Events**:
- If email follows a scheduled meeting/call and asks for updates, next steps, or status → Needs Response
- Phrases to catch: "following up", "any updates", "wanted to check in", "next steps"
- Extra urgency if sender is waiting on user for a decision or action

### Needs Action
**Criteria**: User must do something non-reply (review, approve, decide, upload, etc.)
- Direct request for user to take specific action
- User is accountable for deliverable or decision
- Cannot be handled by someone else on the team

**Introduction/Handoff Emails**:
- If email introduces user as "point of contact" or states user "will coordinate" → Needs Action
- Even if user is CC'd, explicit assignment of responsibility = action required
- Example: "{user's name from me.md} will be your point of contact from here"

**Completion/Handoff Confirmations**:
- If email confirms completion of something user requested → Needs Action
- Status updates that signal "your turn now" = action required, not FYI
- Check thread context: did user initiate the request being completed?
- Example: "Introductions have been sent" (after user asked for intros)

### Optional Response
**Criteria**: Polite to respond but not required
- User could add value but response not essential
- Social or courtesy responses (thanks, congratulations, etc.)
- Internal team updates where acknowledgment is appreciated

### FYI
**Criteria**: Awareness only, no action needed
- User copied on group emails for context
- Status updates where others are handling
- Automated notifications that impact active projects
- Confirmations where others have responded adequately
- **Financial/Accounting Emails**: User is typically copied for visibility on invoices, payments, and financial matters unless specifically called out by name

## Exclusions

### Automatic Exclusions (Never Include)
- **Group Email Addresses**: 
  - `aaas@jetfuel.agency` (agency accountant)
  - `accountingdept@jetfuel.agency` (accounting department)  
  - `agencyaccountant@jetfuel.agency` (agency accountant variant)
- **Marketing/Newsletter Content**:
  - Emails with unsubscribe links in footer
  - Promotional content from services (Gusto newsletters, payment processor updates, etc.)
  - Weekly/monthly digest emails from business tools
  - Event invitations from vendors (unless directly relevant to active projects)
- **Automated Receipts & Notifications**:
  - Payment receipts sent to accounting groups
  - Automated billing notifications
  - System notifications that don't require action

### System-Generated Edge Cases (No Labels)
For emails that slip through query patterns, skip if sender matches:
- `clickup@email.clickup.com` - ClickUp uses non-standard sender format
- `*@smartrecruiters.com` - Recruiting platform notifications (not candidate emails)
- `*@calendly.com` - Booking confirmations (track in calendar)

**Rule**: If uncertain whether sender is automated, check for "unsubscribe" link or bulk mail indicators. When in doubt, include in digest.

### Conditional Exclusions  
- Group emails where someone else has already responded and resolved the matter
- Threads where user was only CC'd for visibility and no direct action is needed
- Marketing emails from business tools UNLESS they impact active projects or decisions

## Date Aging System
Format pending duration to show urgency:
- **Current week**: "Today", "Tuesday", "Wednesday" 
- **Previous week**: "Last Monday", "Last Friday"
- **Older**: "Last Monday (8/28)", "Two weeks ago (8/15)"
- **Very old**: "Last month (7/15)", "Two months ago (6/10)"

## Ordering
- Within each section: oldest to newest
- Show age prominently so user can prioritize

## Voice & Format
- Statement tone, not questions unless essential
- One line context per item that explains the ask/situation
- Include clickable email links: [open link](gmail-url)
- Be specific about what's needed from user

## Thread Analysis
- Read entire thread to understand context
- Check if someone else has already resolved the matter
- Look for user's previous commitments or promises in the thread
- Identify if user is primary contact or just copied for awareness

## Processing Methodology

### Batch Processing Requirements
When processing large email volumes via batch/metadata methods:

**Always Pull Full Thread Content For**:
1. **Direct 1:1 threads** - User is sole recipient with external person
2. **Recruiting/Interview threads** - Time-sensitive, people waiting
3. **Threads with 3+ messages** - Indicates active back-and-forth requiring context
4. **Follow-up keywords in subject** - "Re:", "Following up", "Update", "Status"

**Metadata-Only Acceptable For**:
- Newsletters/marketing (auto-exclude anyway)
- System notifications
- Group distribution emails where user is CC'd
- Single-message FYI forwards

### Priority Weighting
When flagging items, weight by relationship type:
1. **Highest**: Direct 1:1 external (candidates, vendors, direct clients)
2. **High**: Client threads where user is named contact
3. **Medium**: Team threads requiring user input
4. **Lower**: Group/CC threads for awareness

## Team Communication Guidelines

**User preferences** (read from `me.json`):
- `skills._shared.team_members` — colleagues whose emails are likely FYI when they're handling things
- `skills._shared.role_context` — determines which email topics are relevant vs. noise
- `skills.email-update.preferences.priority_topics` — topics to flag even when user is CC'd
- `skills.email-update.preferences.financial_emails` — `"skip"` (default) or `"flag"` for financial/accounting emails

**Internal team emails (colleagues to clients with user CC'd):**
- **Default**: FYI (user copied for awareness, team member handling). Use `role_context` to determine relevance — prioritize emails matching the user's role, deprioritize unrelated topics.
- **Needs Action**: Only if work requires user's specific review/approval before proceeding
- **Priority boost**: If email topic matches `priority_topics`, bump classification up one level (FYI → Optional Response, Optional Response → Needs Action)
- **Key question**: Does user need to personally act, or is team member managing the relationship?

**Completed work notifications:**
- **FYI**: If team member is managing client relationship and feedback
- **Needs Action**: If user must review quality or approve before client delivery

## Timing
- Target delivery: 8:00 AM PST
- Process emails from previous day's last update checkpoint
- Preserve unread status for emails user hasn't opened yet
