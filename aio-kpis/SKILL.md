---
name: aio-kpis
description: Measure the AIO / AI-visibility scorecard KPIs (Qualified AI Visibility, Competitive Share of Voice, AI Recommendation Rate, Owned Citation Rate, AI-Referred Conversions) for a client against a frozen prompt panel. Use for "run the AI visibility KPIs", "AIO scorecard", "AI visibility score for <client>", or refreshing the panel measurement. Panels live in panels/<client>.json.
---

# AIO KPIs

Computes the five scorecard KPIs from the AIO Dashboard KPI Framework. Design doc:
https://docs.google.com/document/d/1wcTafTjM4soJZ5R2sujOVRZxX6PyKSP2vuB8_ECw_L8

## Architecture (durable + token-efficient)

- **Frozen panel on disk** (`panels/<client>.json`), built once from real GSC demand + Ahrefs
  keyword expansion + live AI-retrieval research. Never regenerated per run. Bump `panel_version`
  if you change prompts (measurement continuity depends on a stable panel).
- **All LLM calls + aggregation happen in `runner.py` (Python).** Raw responses never enter the
  model context. The runner writes a small results JSON; that is all you read back.
- **Provider-agnostic.** The runner queries whatever LLM APIs have credentials in the environment
  and skips the rest. It reads keys at its own runtime; do not paste keys into context.
  - Gemini (web-grounded): `GEMINI_API_KEY` or `GOOGLE_API_KEY` (uses `google.genai`), or Vertex via
    `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_CLOUD_PROJECT` + ADC.
  - Perplexity (web-grounded): `PERPLEXITY_API_KEY`.
  - OpenAI/ChatGPT (web_search tool): `OPENAI_API_KEY`.
- **Caching / delta cadence.** Raw responses are cached per (panel, provider, prompt, date) so a
  same-day re-run is free. History is appended to `history/<client>.jsonl` for time series.

## Why Brand Radar is not used

Ahrefs Brand Radar would be the obvious source, but our Ahrefs plan does not carry the Brand Radar
LLM addon (confirmed 2026-07-24: `brand-radar-*` returns "Missing addon"). We run the panel ourselves.

## Usage

```
python .claude/skills/aio-kpis/runner.py --panel jinx --providers gemini,perplexity
python .claude/skills/aio-kpis/runner.py --panel jinx --list-providers   # show which are active
```

Then read `results/<client>_<date>.json` and report the KPI values. Rules:

- Always show **sample size + reliability grade (A-D)** with every KPI. Label estimates as modeled.
- Use the defensible reporting language from the framework ("appeared in X% of the panel", never
  "X% of all ChatGPT searches").
- **Per-client lens overrides.** Read `panels/<client>.json -> meta.client_context`. For Jinx it is
  AWARENESS-FIRST by design: KPI 5 (AI-Referred Conversions) is a SECONDARY/directional signal only;
  branded-search lift + retail store visits are the truer outcome. Never read low conversions as a
  tracking failure for Jinx.

## KPI 5 (AI-Referred Conversions): separate, GA4-based

Not part of runner.py. Pull from the client GA4 property (`meta.ga4_property_id`) via the GA4 Data
API using the marketing@ ADC (`C:\Users\assem\.claude\secrets\ga4-user-adc.json`): dimension
`sessionSource` matched to the AI-referrer allowlist (chatgpt.com, chat.openai.com, perplexity.ai,
gemini.google.com, copilot.com, claude.ai), metrics `sessions`, `keyEvents`, `totalRevenue`.
