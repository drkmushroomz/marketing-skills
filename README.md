# Marketing Skills for Claude Code

AI-powered marketing automation skills built for [Claude Code](https://claude.com/claude-code). This is the single source of truth — clone this repo into any jetfuel-crew workspace.

## Skills

### `/publish-blog`
Google Doc → WordPress draft with rich media, infographic visualizations, TOC, FAQ schema, auto-generated featured image, and LLM competitiveness audit.

### `/seo-opportunities`
Pulls Google Search Console data, identifies ranking opportunities, content gaps, and quick wins across target niches. Outputs to Google Sheets with weekly top-5 priorities.

### `/paid-ads`
Full paid advertising strategy framework — campaign structure, audience targeting, creative best practices, optimization playbook, retargeting strategies. Pulls context from HQ, Slack, Gmail, Drive, and ClickUp before making recommendations.

### `/llm-prompt-research`
Research and validate LLM prompts a brand should target for AI visibility. Uses Brandi AI / Wellows methodology with real conversational patterns, not keyword strings.

### `/page-cro`
Page conversion rate optimization — analyze landing pages, identify friction, recommend improvements with A/B test setup.

### `/audience-audit`
Audience analysis and segmentation for ad targeting and content strategy.

### `/transcribe-podcast`
Transcribe podcast audio with speaker diarization using faster-whisper (local, no API keys). Outputs to Google Drive.

### `/write-content`
Write SEO + AIO optimized content for jetfuel.agency.

## Setup

### Install to a new machine:
```bash
# From your jetfuel-crew project root:

# Copy skills
cp -r marketing-skills/skills/* .claude/ops/
cp -r marketing-skills/skills/* .claude/skills/  # for team-managed skills

# Copy commands
cp marketing-skills/commands/* .claude/commands/

# Copy scripts
cp marketing-skills/scripts/* scripts/

# Install dependencies
pip install Pillow requests faster-whisper google-ads google-auth google-auth-oauthlib google-api-python-client playwright
python3 -m playwright install chromium
```

### Required config (in `.claude/me.json`):
```json
{
  "wordpress": {
    "app_password": "your-wp-app-password"
  }
}
```

### Required auth:
- Google OAuth tokens in `scripts/gads_tokens.json` (run `scripts/gsc_auth.py` to generate)
- WordPress application password (generate in wp-admin → Users → Application Passwords)

## Directory Structure

```
skills/
  publish-blog/       — PROMPT.md, config.json
  seo-opportunities/  — PROMPT.md, config.json
  paid-ads/           — SKILL.md, references/
  llm-prompt-research/ — SKILL.md
  page-cro/           — SKILL.md, references/, evals/
  audience-audit/     — audience_auditor.py, config.json
  transcribe-podcast/ — PROMPT.md
commands/             — Slash command entry points (.md files)
scripts/              — Python scripts for API access, image gen, publishing
```

## License

MIT
