# Jetfuel Meta Ads Skills

The 10 `/jf-*` skills in this folder are Jetfuel-specific adaptations of the public skills documented at [heyoz.com/blogs/claude-code-skills-for-meta-ads](https://heyoz.com/blogs/claude-code-skills-for-meta-ads).

They differ from the generic versions in four ways:

1. **Anchored in the JF Andromeda playbook.** Every skill cites `project_andromeda_audit_rubric.md` (the 14-point lens), `feedback_meta_ads_2026.md` (no lookalikes, creative-as-targeting), and the blog drafts `02-andromeda-algorithm.md` through `07-brand-consistency-moat.md`.

2. **HQ-first, Meta MCP for execution, no DIY HTTP.** Reads + writes go through `mcp__jetfuel-hq__*` for client/campaign/insight data and `mcp__meta__*` for live Meta calls. No bearer-token scripts (`feedback_no_mcp_http_scripts.md`).

3. **Client data, not industry benchmarks.** Per-client target ROAS/CPA come from HQ `get_client_goals`. Thresholds are not global.

4. **Edwin's voice + JF guardrails.** Hooks pass `edwin-tone-guide.md` filter. Skills never auto-pause client spend (`feedback_no_pause_client_spend.md`). Skills never fabricate data (`feedback_no_fabricated_data.md`).

## The 10 skills

| Slug | Generic equivalent | Headline difference |
|---|---|---|
| `jf-spy` | `/spy` | Uses HQ Ad Recon brands + diffs against last pull + classifies against JF 12-theme/4-tone taxonomy. Surfaces market trends (≥2 competitors converging) and proposes specific tests for the client. |
| `jf-bulk-creative` | `/bulk-creative` | Produces production briefs across structural axes (tone × persona × funnel × format), not Puppeteer renders. Prices the plan against the JF easy/medium/hard sourcing tiers (UGC ~$83 / AI ~$0.17 / in-house ~$6000). |
| `jf-deploy-ads` | `/deploy-ads` | Uses Meta MCP (not raw Graph). Defaults to JF Andromeda structure (Scale ASC / Manual Retargeting / Sandbox). Refuses lookalikes. Never publishes without explicit confirmation. |
| `jf-bleed-check` | `/bleed-check` | Per-client thresholds from HQ goals (not global $50). Sandbox carve-out (sandbox is allowed to lose). Alerts only — never auto-pauses. Posts to client-mapped Slack channels. |
| `jf-fatigue-scan` | `/fatigue-scan` | Two-layer diagnosis: Layer 1 (perf decline) + Layer 2 (emotional/theme monotony — the actual root cause per the JF playbook). Pipes replacement briefs to `/jf-bulk-creative`. |
| `jf-rebalance` | `/rebalance` | Respects the JF 3-bucket structure (Scale/Retargeting/Sandbox each rebalanced by its own rules). Surfaces graduation candidates from Sandbox → Scale. Never pauses. Capped per-run shifts to preserve Meta learning. |
| `jf-setup-capi` | `/setup-capi` | Targets EMQ 9.3 (the Aletha benchmark). Audits current state before generating code. Recommends Aimerce/Elevar as the enhancement vendor based on JF Aletha implementation path. |
| `jf-hooks` | `/hooks` | Varies across the axes Andromeda actually cares about (tone × theme × persona × funnel), not PAS/BAB/AIDA frameworks. Hard filter against Edwin's anti-AI-tells list (`edwin-tone-guide.md`). |
| `jf-meta-audience-audit` | `/audience-audit` | Meta-specific (the existing `/audience-audit` is Google). Flags lookalikes, interest stacking, missing purchaser exclusions, TOF/MOF/BOF silos. Outputs Mermaid architecture + migration plan. |
| `jf-weekly-report` | `/weekly-report` | Per-client HQ goals (not global). Layers Andromeda 14-point score so accounts with great metrics but a brittle creative engine get flagged early. Routes per-client Slack via channel mapping. |

## Workflow chains

Skills are designed to compose. Typical sequences:

**Monday morning** → `/jf-weekly-report` → identifies clients needing attention → strategist drills in with `/jf-fatigue-scan` and `/jf-meta-audience-audit` for the flagged accounts.

**New client onboarding** → `/jf-setup-capi` (week 1) → `/jf-meta-audience-audit` to baseline the inherited account → `/jf-bulk-creative` for first creative wave → `/jf-deploy-ads --mode=draft --bootstrap` to spin up the JF Andromeda structure.

**Weekly creative cycle** → `/jf-fatigue-scan` → identifies shortfall → `/jf-bulk-creative` with the gap tones/personas pre-filled → `/jf-hooks` to generate copy variations per brief → `/jf-deploy-ads --mode=draft` to load the warehouse → human reviews + activates.

**Competitive intelligence** → `/jf-spy` weekly → spot market trends → `/jf-bulk-creative` to fill the gap → `/jf-deploy-ads --target=sandbox` to test.

**Budget hygiene** → `/jf-bleed-check` every 6h (cron via Windows Task Scheduler) → human responds to alerts → `/jf-rebalance` weekly for non-emergency shifts.

## Sources of truth (canonical references)

- `project_andromeda_audit_rubric.md` — 14-point lens
- `feedback_meta_ads_2026.md` — no lookalikes / creative-as-targeting
- `feedback_no_pause_client_spend.md` — never auto-pause
- `feedback_no_mcp_http_scripts.md` — use native MCP tools
- `feedback_no_fabricated_data.md` — placeholders, not invented numbers
- `feedback_content_voice.md` — anti-AI-tells
- `feedback_local_cron.md` — Windows Task Scheduler for scheduled runs
- `edwin-tone-guide.md` — voice + verbal patterns
- `blog-drafts/01-creative-production-formula.md` — decay × win × budget formula
- `blog-drafts/02-andromeda-algorithm.md` — variant strategy died
- `blog-drafts/03-three-bucket-method.md` — content gap analysis
- `blog-drafts/05-emotional-creative-fatigue.md` — 4-tone framework
- `blog-drafts/06-ten-to-hundred-ads.md` — easy/medium/hard sourcing
- `tools/andromeda-readiness-audit/` — the free self-assessment tool that productizes the same rubric

## Known dependencies

- HQ MCP must be loaded (`load_clients_tools`, `load_ads_tools`, `load_recon_tools` for the recon-using skills).
- Meta MCP is required for live ad operations. The `meta_ad_library_search` endpoint is gated at the App level (see `reference_meta_ad_library_api.md`); skills using it have HQ Ad Recon fallback paths.
- Slack MCP for alert posting (`mcp__claude_ai_Slack__slack_send_message`).
- Google Workspace MCP for Sheet deliverables.

## Where the configs live

Each skill has a paired `.claude/ops/<skill-name>/config.json`. Client-specific mappings (HQ client IDs, Slack channels, target ROAS, budget caps) belong in those configs, not hardcoded in the skill.

When onboarding a new client into these workflows, populate the relevant `clients.{slug}` block in each skill's config before running the skill for that client.
