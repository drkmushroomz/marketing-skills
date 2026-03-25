Help with paid advertising campaigns — strategy, targeting, optimization, and setup.

Read the skill at `.claude/ops/paid-ads/SKILL.md` and the reference docs in `.claude/ops/paid-ads/references/`.

For Jetfuel clients, gather full context before making recommendations:

1. **HQ data** — check connected ad platforms via `hq_get_client_platforms`, pull campaign data via `hq_list_campaigns` / `hq_get_campaign_insights`, and review any audit findings via `hq_list_audits` / `hq_get_audit_detail`
2. **Slack** — search recent messages about the client in relevant channels (use `slack_search_public` with the client name) to catch latest updates, concerns, or strategy shifts from the team
3. **Email** — search Gmail for recent client threads (use `search_gmail_messages` with client name/domain) to find the latest performance reports, client feedback, or requests
4. **Meeting transcripts** — check Google Drive for recent meeting notes or transcripts (use `search_drive_files` with client name) to pull context from recent calls
5. **ClickUp** — search for active tasks related to the client (use `clickup_search` with client name) to see what's in progress

Synthesize all of this before giving advice. The most recent Slack message or meeting note often has context that overrides what the data says.

For direct Google Ads API access, use the scripts in `scripts/` (gads_keywords.py, gads_auth.py) with the OAuth tokens in `scripts/gads_tokens.json`.

$ARGUMENTS
