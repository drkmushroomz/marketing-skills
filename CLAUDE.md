# Marketing Skills for Claude Code

AI-powered marketing automation skills for Claude Code. This repo is the single source of truth for all marketing skills — clone it into any jetfuel-crew workspace.

## Repository Structure

- `skills/` — Skill definitions (PROMPT.md/SKILL.md + config.json per skill)
- `commands/` — Slash command entry points (.md files)
- `scripts/` — Python scripts for API access (Google Ads, GSC, WordPress, transcription)
- Top-level directories (e.g. `paid-ads/`, `seo-audit/`) — Extended skill resources, references, and evals

## Key Skills

- `/publish-blog` — Google Doc → WordPress draft with rich media and SEO
- `/seo-opportunities` — GSC data analysis, ranking opportunities, content gaps
- `/paid-ads` — Campaign strategy, audience targeting, creative optimization
- `/page-cro` — Landing page conversion rate optimization
- `/write-content` — SEO + AIO optimized content creation

## Development Guidelines

- Skills follow a standard structure: `PROMPT.md` or `SKILL.md` for the prompt, `config.json` for metadata
- Python scripts in `scripts/` handle external API integrations (Google, WordPress)
- Do not commit secrets, tokens, or credentials (`.env`, `me.json`, `*_tokens.json`)
- When adding a new skill, create both the skill directory and a corresponding command in `commands/`
