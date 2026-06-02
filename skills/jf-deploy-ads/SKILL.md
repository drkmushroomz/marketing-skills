---
name: jf-deploy-ads
description: "Deploy a Jetfuel creative manifest to Meta as paused (warehouse) or live (shelf) ads using the Meta MCP. Defaults to Andromeda-compliant structure: 1 ASC + 1 manual retargeting + 1 sandbox campaign, 70-80/15-20/5-10 budget split, no lookalikes, no interest-stacking. Use when the user says 'deploy these creatives', 'launch the campaign', 'push to Meta', 'spin up the sandbox', 'graduate this to scale', or hands you a manifest from /jf-bulk-creative."
disable-model-invocation: true
---

# /jf-deploy-ads — Meta Deploy (Jetfuel)

Takes a manifest from `/jf-bulk-creative` (or a hand-written manifest) and builds the campaigns / ad sets / ads in Meta via the Meta MCP. Defaults to JF's 2026 Andromeda structure. Supports `draft` (PAUSED warehouse) and `publish` (ACTIVE shelf) modes.

Built on top of `mcp__meta__*` tools (we own this access — not the gated Ad Library endpoint), with HQ writeback so the client view in HQ stays in sync.

## Architecture defaults (the JF posture)

Per `project_andromeda_audit_rubric.md` and `feedback_meta_ads_2026.md`:

```
Account
├── Scale ASC (70–80% budget) — Advantage+ Sales, broad audience, all winning variations
├── Manual retargeting (15–20%) — visitors / cart / checkout abandoners
└── Sandbox (5–10%) — new concepts, low budget, graduates feed the Scale ASC
```

We do not create:
- Lookalike audiences (1%/3%/5% deprecated)
- Interest-stacked ad sets
- TOF/MOF/BOF prospecting silos
- Multi-campaign clutter for the same objective

We do create:
- Broad ASC with creative diversity (the actual targeting in 2026)
- One manual retargeting layer with funnel-stage messaging
- A small sandbox sized to spawn one structural test per week

## Arguments

- Client name (must match HQ client). Default: ask.
- `--manifest path` — JSON manifest from `/jf-bulk-creative`. Default: most recent for the client.
- `--mode draft|publish` — Default: `draft` (warehouse). Switch to `publish` only with explicit user confirmation.
- `--target sandbox|scale|retargeting|auto` — which campaign to deploy into. Default: `auto` — sandbox for new concepts, scale for graduates.
- `--budget-split "70,15,15"` — Scale/Retargeting/Sandbox percentages. Must sum to 100. Default from config.
- `--total-daily-budget USD` — total account daily. Default: read current spend from `client_performance` last 7d.
- `--dry-run` — validate + estimate API calls, don't execute.

## Steps

### 1. Load identity, manifest, account context

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-deploy-ads/config.json` for client → meta_account_id, page_id, pixel_id, default budget splits, approved budget caps.
- Load the manifest (default: most recent at `.claude/ops/jf-bulk-creative/manifests/{client}-*.json`).
- Resolve HQ client → `get_client_platforms` → find `meta_account_id` (or fall back to `mcp__meta__meta_list_ad_accounts`).

### 2. Validate the manifest

Every variation must have: id, format, hook, primary_text, headline, cta, visual_direction, asset_path (or `pending` if the brief hasn't been produced yet). Reject if:
- More than 25% of variations cluster in one core message (Andromeda compression risk — bounce back to `/jf-bulk-creative`).
- Any variation makes an unapproved claim (cross-reference client brief).
- Budget split doesn't sum to 100.
- `--mode publish` but `--target scale` and the variation set hasn't graduated from sandbox (no historical win data) — refuse and warn.

If `--dry-run`, output the validation report and stop.

### 3. Discover or create the three campaigns

Use `mcp__meta__meta_list_campaigns(account_id={id})` to find:
- `JF_Scale_ASC_{Client}` (Advantage+ Sales)
- `JF_Retargeting_Manual_{Client}` (Sales)
- `JF_Sandbox_{Client}` (Sales, lower budget)

If any are missing, **DO NOT silently create them in publish mode**. Print:
```
Missing campaigns: [list]
This account doesn't have the JF Andromeda structure. Recommend running:
  /jf-deploy-ads --mode=draft --bootstrap
to create the three campaigns paused. Then graduate.
```

`--bootstrap` is the only auto-creation flag. Without it, this skill only adds to existing campaigns.

### 4. Resolve creative assets

For each variation in the manifest:
- If `asset_path` is local: upload via the Meta MCP image/video endpoint (use the `mcp__meta__*` upload tool — not raw graph API).
- If `asset_path` is `pending`: skip with a "pending production" note and do not create the ad.
- If the asset references an existing `image_hash` or `video_id` in the account: reuse.

### 5. Build the ad set(s)

**Scale ASC** (default for graduated winners):
- Optimization: OFFSITE_CONVERSIONS, Purchase
- Audience: Advantage+ default (no exclusions except current purchasers)
- Budget: `--total-daily-budget * scale_pct`
- Placements: Advantage+ all placements
- No lookalikes, no interest stacking — period.

**Sandbox** (default for new concepts):
- One ad set per emotional tone × format combination (max 4-6 ad sets)
- Budget: `--total-daily-budget * sandbox_pct / count`
- Audience: Advantage+ Audience (broad, no constraints)
- Each ad set holds 3-5 variations of the same tone/format axis (testable unit)

**Retargeting** (only if manifest contains MOFU/BOFU variations):
- Audience: pixel-based — visitors 30/60d, ATC 14d, ICO 7d (created if missing via `mcp__meta__*` custom audience tool)
- Exclude purchasers
- Budget: `--total-daily-budget * retargeting_pct`

### 6. Create ad creatives + ads

For each variation routed to its target ad set:
- Build the ad creative (`object_story_spec` with page_id + link_data + image_hash/video_id).
- Build the ad with name = manifest `id` (this is what makes the naming convention queryable later in `/jf-fatigue-scan` and HQ reporting).
- Status: PAUSED if `--mode=draft`, ACTIVE if `--mode=publish`.

Rate-limit: 0.5s between creates. Retry HTTP 429 once after 60s. Skip + log HTTP 400. Stop on 401 (token).

### 7. Mirror to HQ

After creation, hit HQ so `list_creative_ads` reflects the new state:
- For each new ad: HQ recon-ingest is asynchronous (24h), but immediate insight pulls go via `get_campaign_insights` once Meta starts serving impressions.

### 8. Write the deploy report

`.claude/ops/jf-deploy-ads/reports/{client}-{YYYY-MM-DD-HHmm}.md`:

```
# Deploy — {Client} — {timestamp}

## Mode: draft|publish
## Budget split: {scale}/{retargeting}/{sandbox}%

## Created
- Scale ASC: {n} ads added
- Sandbox: {n} ads added across {m} test ad sets
- Retargeting: {n} ads added

## Skipped (pending production)
- {variation_id}: {reason}

## Errors
- {variation_id}: HTTP {code} — {message}

## Ads Manager deep links
- ASC: https://business.facebook.com/...
- Sandbox: ...

## Total API calls: {n}
```

### 9. Present summary

```
{n} ads created in {client}'s Meta account, all PAUSED.
Andromeda check: {x}/14 (theme diversity, tone diversity, format diversity, retargeting present).
Sandbox tests: {m} new structural angles ready.
Want me to activate? (Recommend reviewing the manifest in {sheet_link} first.)
```

## Important Rules

- **Default mode is `draft` (PAUSED).** Never publish without explicit user confirmation in the conversation, even if `--mode=publish` is passed — re-confirm because going live spends money.
- **`--bootstrap` is the only auto-create flag.** Without it, only add ads to existing campaigns. Never silently create new campaigns inside `publish` mode.
- **No lookalike audiences. Ever.** If a manifest or arg requests one, refuse and cite `feedback_meta_ads_2026.md`.
- **No interest-stacking.** Advantage+ Audience only.
- **Budget caps from config.** If `--total-daily-budget` exceeds the approved client cap in config, refuse and ask for explicit override.
- **Existing client spend protected.** Per `feedback_no_pause_client_spend.md` — don't pause anything via this skill unless `--allow-pause` is explicitly passed. New deploys add, they don't replace.
- **Display all times in user's timezone.**
- **Naming convention is the audit trail.** Every ad name must match `{Client}_{Tone}_{Persona}_{Funnel}_{Format}_v{NN}` from the manifest, or `/jf-fatigue-scan` and HQ reporting can't slice by tone/persona.
- **HQ writeback is best-effort.** If HQ sync fails, log it but don't roll back the Meta creates.
- **Token failure stops everything.** On HTTP 401, halt immediately and tell the user to refresh.

## Config

`.claude/ops/jf-deploy-ads/config.json`:

```json
{
  "clients": {
    "hampton-water": {
      "hq_client_id": 37,
      "meta_account_id": "act_xxx",
      "page_id": "...",
      "pixel_id": "...",
      "approved_daily_budget_cap_usd": 800,
      "default_budget_split": {"scale": 75, "retargeting": 15, "sandbox": 10},
      "default_objective": "OFFSITE_CONVERSIONS",
      "default_optimization_event": "Purchase",
      "campaign_names": {
        "scale": "JF_Scale_ASC_HamptonWater",
        "retargeting": "JF_Retargeting_Manual_HamptonWater",
        "sandbox": "JF_Sandbox_HamptonWater"
      }
    }
  }
}
```

## Why this skill exists

External `/deploy-ads` skills hit Graph API directly with bearer tokens copied from env. Per `feedback_no_mcp_http_scripts.md`, that's a no-go for our stack. The Jetfuel version goes through the Meta MCP (we own the OAuth, the SDK is maintained, retries are handled), enforces the Andromeda structural defaults so juniors can't accidentally rebuild the lookalike-era account model, and refuses to overwrite or pause existing client spend without explicit consent.
