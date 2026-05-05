---
name: execution-pipeline
description: "Score and triage SEO keywords into execution tiers based on difficulty, current rankings, and content status. Use when the user wants to prioritize keywords, decide what to write vs delegate, triage a keyword list, or figure out which content to automate vs hand off. Also use when the user mentions 'keyword triage,' 'execution pipeline,' 'content prioritization,' 'what should Claude write vs the team,' 'keyword difficulty triage,' 'content automation,' or 'which keywords to target first.' Works with GSC data, Ahrefs data, or any keyword list."
metadata:
  version: 1.0.0
---

# Execution Pipeline — Keyword Triage & Scoring

Score keywords using an Impact x Confidence model and route them to the right execution tier: fully automated (Claude writes), semi-auto (Claude drafts, human edits), or team-led (human writes, Claude assists).

Adapted from Eric Siu's content_attack_brief.py scoring model, customized for Jetfuel's workflow.

## Prerequisites

- `.env` with `AHREFS_TOKEN` (strongly recommended for KD + volume data)
- Google Search Console access via MCP or Python scripts
- Optional: output from `/trend-scout` or `/seo-opportunities` as input

## Scripts

The `reference/` directory contains Python scripts that can be run standalone or imported:

- **`content_fingerprint.py`** -- Scans WordPress blog, counts topic frequencies, derives keyword seeds
  ```bash
  python3 .claude/skills/execution-pipeline/reference/content_fingerprint.py
  ```
- **`competitor_gap.py`** -- Pulls your + competitor organic keywords from Ahrefs, finds gaps
  ```bash
  python3 .claude/skills/execution-pipeline/reference/competitor_gap.py
  ```
- **`content_attack_brief_ericsiu.py`** -- Eric Siu's reference implementation (full pipeline)

## Input

Accepts keywords from any source:
- **GSC data** from `/gsc-report` or `/seo-opportunities`
- **Trend scout output** from `/trend-scout`
- **Manual list** pasted by user
- **Ahrefs export** (CSV or inline)
- **Content gaps** from `/content-gaps`

## Step 1: Enrich Keywords with Ahrefs

If `AHREFS_TOKEN` is available, batch keywords through Ahrefs Keywords Explorer:

```python
import requests, os, json

token = os.environ["AHREFS_TOKEN"]
keywords = ["keyword1", "keyword2", ...]  # max 50 per batch

resp = requests.get(
    "https://api.ahrefs.com/v3/keywords-explorer/overview",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "select": "keyword,volume,difficulty,cpc,traffic_potential,intents,volume_monthly",
        "keywords": ",".join(keywords),
        "country": "us"
    }
)
data = resp.json()  # data["keywords"] = list of keyword objects
```

Extract per keyword: **volume**, **difficulty** (KD, 0-100), **cpc** (in cents, divide by 100 for dollars), **traffic_potential**, **intents** (object with boolean flags: informational, commercial, transactional, navigational, branded, local), **volume_monthly** (trend).

**Available columns:** keyword, volume, difficulty, cpc, traffic_potential, intents, volume_monthly, volume_monthly_history, global_volume, clicks, cps, serp_features, parent_topic, parent_volume.

If no Ahrefs token, proceed with GSC data only (position, impressions, clicks, CTR).

## Step 2: Score — Impact x Confidence

Every keyword gets two scores (0-10 each). **Priority = Impact x Confidence** (max 100).

### Impact Score (0-10): "How valuable is this keyword if we rank #1?"

| Signal | Criteria | Points |
|--------|----------|--------|
| **Search volume** | >= 10,000 | +3 |
| | 1,000-9,999 | +2 |
| | 100-999 | +1 |
| | < 100 | +0 |
| **CPC** | >= $5.00 | +3 |
| | $2.00-$4.99 | +2 |
| | $0.50-$1.99 | +1 |
| | < $0.50 | +0 |
| **Funnel stage** | BOFU (agency, pricing, vs, hire, cost, services) | +3 |
| | MOFU (how to, guide, strategy, roi, best practices) | +2 |
| | TOFU (what is, definition, trends, statistics) | +1 |
| **Trend direction** | Rising (3-month trend up > 20%) | +1 |
| | Stable | +0 |
| | Declining (down > 20%) | -1 |

### Confidence Score (0-10): "How likely are we to rank?"

| Signal | Criteria | Points |
|--------|----------|--------|
| **Keyword difficulty** | KD <= 10 | +4 |
| | KD 11-25 | +3 |
| | KD 26-40 | +2 |
| | KD 41-60 | +1 |
| | KD > 60 | +0 |
| **Current position** | Already ranking 1-10 | +3 |
| | Ranking 11-20 | +2 |
| | Ranking 21-50 | +1 |
| | Not ranking | +0 |
| **Topic authority** | We have 3+ published posts in this cluster | +2 |
| | We have 1-2 posts | +1 |
| | No existing content | +0 |
| **Content exists** | We have a page targeting this keyword | +1 |
| | No page exists | +0 |

### Funnel Classification

Auto-tag each keyword:

```
BOFU signals: "agency", "company", "service", "pricing", "cost", "hire",
              "vs", "alternative", "review", "best [service]", "near me",
              "for [industry]"

MOFU signals: "how to", "guide", "strategy", "roi", "tips", "examples",
              "template", "checklist", "framework", "best practices",
              "tools for", "software for"

TOFU signals: "what is", "definition", "meaning", "statistics", "trends",
              "benefits of", "types of", "history of"
```

If multiple signals match, use the highest-funnel classification (BOFU > MOFU > TOFU).

## Step 3: Check Content Status

For each keyword, determine if a page already exists on the target site:

1. **GSC query-page matrix** -- does this keyword already drive traffic to a page?
2. **WebSearch** -- `site:{domain} {keyword}` to check for existing content
3. **Content inventory** -- if available from `/content-gaps`

Classify as:
- **Has page, ranking well** (pos 1-10)
- **Has page, needs optimization** (pos 11-50)
- **Has page, not ranking** (pos > 50 or no GSC data)
- **No page exists**

## Step 4: Assign Execution Tier

Based on KD + content status, route each keyword:

| Tier | KD Range | Content Status | Who Does the Work | Workflow |
|------|----------|---------------|-------------------|----------|
| **Tier 1: Full Auto** | KD <= 20 | No page exists | Claude writes, human reviews | `/write-content` generates full draft. Human does 10-min review + publish. |
| **Tier 2: Auto Refresh** | KD <= 50 | Has page, needs optimization | Claude upgrades, human reviews | `/content-gaps` prescribes changes. Claude implements. Human approves. |
| **Tier 3: Semi-Auto** | KD 21-40 | No page exists | Claude drafts outline + first pass, human finishes | Claude writes 70% (structure, research, first draft). Human adds voice, examples, polish. |
| **Tier 4: Team + AI** | KD 41-60 | No page exists | Human writes, Claude assists | Human leads strategy and writing. Claude handles research, data, optimization, internal linking. |
| **Tier 5: Expert Only** | KD > 60 | Any | Human writes fully | High-competition keyword. Needs original research, expert interviews, or unique data. Claude can help with research only. |

**Override rules:**
- BOFU keyword + KD <= 40 = always at least Tier 3 (too important to fully automate)
- Any keyword with CPC > $5 = bump up one tier minimum (high commercial value warrants human attention)
- Trending keyword (from `/trend-scout`) + KD <= 30 = Tier 1 with urgency flag (speed matters)

## Step 5: Output

### Console Report

```
## Execution Pipeline — {domain}
Generated: {date}
Keywords analyzed: {n}

### Pipeline Summary
| Tier | Count | Est. Hours | Description |
|------|-------|-----------|-------------|
| Tier 1: Full Auto | {n} | {n}h | Claude writes, 10-min human review |
| Tier 2: Auto Refresh | {n} | {n}h | Claude upgrades existing pages |
| Tier 3: Semi-Auto | {n} | {n}h | Claude drafts, human finishes |
| Tier 4: Team + AI | {n} | {n}h | Human leads, Claude assists |
| Tier 5: Expert Only | {n} | {n}h | Human writes fully |

### Top 10 by Priority Score
| Keyword | Impact | Confidence | Priority | KD | Volume | Funnel | Tier | Action |
|---------|--------|-----------|----------|-----|--------|--------|------|--------|

### BOFU Money Keywords (act first)
[All BOFU keywords sorted by priority]

### Quick Wins (Tier 1 + Tier 2)
[Keywords Claude can handle with minimal human input]

### Trending + Low KD (time-sensitive)
[Keywords from trend-scout that are easy to rank for]

### Decay Alerts
[Keywords where position dropped > 5 spots in 28 days vs 90-day average]
```

### Google Sheet Output (optional)

If the user requests a sheet, create one with tabs:
1. **All Keywords** -- full scored list with all fields
2. **Tier 1: Full Auto** -- Claude's to-do list
3. **Tier 2: Auto Refresh** -- pages to upgrade
4. **Tier 3-5: Team Queue** -- human assignments
5. **Summary** -- pipeline stats

### JSON Output

Save to `output/execution-pipeline-{date}.json` for programmatic use.

## Integration

| Feeds Into | How |
|-----------|-----|
| `/write-content` | Tier 1 keywords become blog post assignments |
| `/content-gaps` | Tier 2 keywords become refresh candidates |
| `/trend-scout` | Trending keywords get pipeline-scored for urgency |
| `/seo-opportunities` | Pipeline scoring replaces the simpler impressions-based priority |
| `/abm-content` | High-impact keywords inform ABM content topics |

## Recommended Cadence

- **Weekly:** Run full pipeline with fresh GSC + Ahrefs data
- **After trend-scout:** Score any new trending keywords immediately
- **Monthly:** Review pipeline output vs actual rankings to calibrate scoring weights
