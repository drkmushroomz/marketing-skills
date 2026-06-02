# Persona Research Methodology

Encoded from four public frameworks + the HQ Recon tools. Replaces the "eyeball the screenshot and guess" approach that the May 19 Flora audit got called out for.

Public frameworks layered in:
1. **Eugene Schwartz — 5 Levels of Awareness** ([Motion App's DTC adaptation](https://motionapp.com/blog/five-customer-awareness-stages-advertising))
2. **Jobs-to-be-Done (JTBD)** — Bob Moesta / Tony Ulwick / Clayton Christensen ([Strategyn](https://strategyn.com/jobs-to-be-done/), [CXL JTBD interviews](https://cxl.com/blog/customer-interviews/))
3. **Corey Haines's customer-research skill** ([coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills/blob/main/skills/customer-research/SKILL.md)) — JTBD-functional/emotional/social, frequency × intensity ranking, confidence labels, 5–10 data-point minimum
4. **takechanman1228/claude-persona** ([github](https://github.com/takechanman1228/claude-persona)) — AI persona panels for hypothesis validation

Internal sources of evidence:
- **HQ Recon** (`list_recon_hooks`, `get_recon_brand_analytics`, `list_recon_ads`) — the primary truth source. Hooks are ranked by **days running**, which is HQ's proxy for what's actually converting. A 246-day-old hook beat the algorithm's pause threshold every day, so it's market-validated.
- HQ `get_context_events` (client mode only) for declared promo / strategy context
- Klaviyo flow data and HQ `creative_tag_analytics` (client mode only)

---

## The Iron Rules

These come straight from Corey Haines's skill, adapted to ad-based persona work.

1. **No persona without 3+ market-validated hooks pointing to the same job-cluster.** (Lower than Corey's "5–10 data points" because each hook is itself a synthesis of many tests; we're treating market longevity as the validation signal.)
2. **Don't average across distinct personas.** Two adjacent personas with different jobs go in separate buckets even if they share demographics.
3. **Capture exact ad copy, not paraphrases.** Verbatim hooks become persona vocabulary.
4. **Label every persona with confidence: High / Medium / Low.**
   - **High** = 3+ longest-running ads (>90 days) pointing at the same job + competitor signal confirms relevance
   - **Medium** = 1–2 ads pointing at a job, OR competitor signal supports it
   - **Low** = inferred from a single ad or theoretical
5. **Don't invent demographics.** If we don't know age/income/location, leave it blank or label it as inference.
6. **Cross-reference, don't echo.** If the persona is just a restatement of the brand's own positioning copy, it's not a real persona — it's marketing collateral.

---

## The Workflow (Step-by-Step)

### Step 1. Source the evidence

**Prospect mode** (no HQ ad-account access):
- `search_recon_brand_candidates(query=<brand>)` → resolve Meta page_id
- If `already_tracked: false` → `preview_add_recon_brand` + `add_recon_brand` → wait ~5 seconds for scrape
- If `already_tracked: true` → proceed directly
- `get_recon_brand_analytics(brand_id)` → media mix + top 5 longest-running hooks
- `list_recon_hooks(brand_id, limit=25)` → full hook table with days_running
- `list_recon_ads(brand_id, sort="longest_running", limit=25)` → full ad list with primary_text, headline, link_url, started_running_at
- `list_recon_landing_pages(brand_id)` → LP distribution (may be empty for newly-added brands — derive from `link_url` in ad list as fallback)

**Client mode** adds:
- `creative_tag_analytics` filtered by `category_slug=persona` or `intent` → AI-tagged persona-per-ad data
- `top_creatives` → highest-ROAS ads (overrides longevity for client-mode signal)
- `get_context_events(client=<name>, types=["client_request","creative_decision","client_sentiment"])` → declared target-customer context from meeting recaps
- If transcripts/reviews exist: pull VOC sources per Corey Haines's customer-research skill

### Step 2. Extract JTBD from each evidenced hook

For each hook in the longevity-ranked list (top 10), identify:

| Dimension | Question |
|---|---|
| **Functional job** | What concrete task is this ad helping the customer accomplish? |
| **Emotional job** | What feeling does this hook trigger or promise? |
| **Social job** | How does buying / using this product change how the customer is perceived? |
| **Trigger** | What moment in the customer's life prompts them to act? |
| **Pain (explicit or implicit)** | What's the named or implied dissatisfaction with the status quo? |
| **Vocabulary** | What exact phrases does the hook use? |

### Step 3. Map each hook to a Schwartz awareness stage

Use Motion's DTC recipe:

| Stage | Hook signature | Examples |
|---|---|---|
| **Unaware** | Storytelling only, no product, no problem | "What if your morning routine was actually aging you?" |
| **Problem-Aware** | Validates a felt pain, no solution yet | "You've probably never had pasta done right." |
| **Solution-Aware** | Comparison / "here's what works" | "POV: I finally tried the viral Italian haul." |
| **Product-Aware** | Brand-specific claim, differentiation | "Flora Biscotti are oven-baked with real ingredients." |
| **Most-Aware** | Product-named, offer-focused, urgency | "Flora pasta sauces." + "Shop Now" |

### Step 4. Cluster jobs → derive personas

JTBD-first, persona-second (Tony Ulwick's invariant). Group hooks that share a job-cluster. Each cluster with 3+ hooks becomes a candidate persona.

For each persona, fill this template (Corey Haines structure, adapted for ad-evidence):

```
Persona name: [descriptive, not cute — "The Real-Italy Seeker", not "Mama Mia Mary"]

Functional job: [verb + outcome]
Emotional job: [feeling]
Social job: [perception]

Trigger: [moment they decide to act]
Top pain: [#1 pain in their words]

Desired outcome: [success in their words + measurable signal]
Vocabulary they use: [verbatim phrases pulled from hooks]
Hook style that resonates: [stage + format]
Awareness stage they enter from: [Schwartz stage]

Evidence (hooks + days running):
- "[hook 1]" (N days)
- "[hook 2]" (N days)
- "[hook 3]" (N days)

Confidence: [High / Medium / Low]

Where they live (channels): [inferred from ad placement / landing pages]
What they buy: [SKUs / categories surfaced in matching ads]
```

### Step 5. AI panel validation (claude-persona pattern)

For each candidate persona, run an Agent panel:
- Generate 5 simulated panel members matching the persona dimensions
- Show them each top hook
- Ask each: "Would this hook land on you? Why or why not? What about it works / doesn't?"
- Cluster reactions thematically
- Flag where the brand is talking to one persona but ignoring an adjacent one with a stronger signal

Use the `Agent` tool with `subagent_type=general-purpose` for the panel. Prompt template at the bottom of this file.

### Step 6. Competitor cross-reference

Run Steps 1–4 against each top organic competitor (`mcp__ahrefs__site-explorer-organic-competitors` to discover; add to Recon if not tracked). Build a side-by-side persona matrix:

| Job/Persona | Us | Competitor A | Competitor B | Competitor C |
|---|---|---|---|---|
| Job 1 | ✓ (3 hooks) | ✓ (5 hooks) | — | ✓ (2 hooks) |
| Job 2 | — | ✓ (4 hooks) | ✓ (2 hooks) | — |

Cells where competitors are present but the audited brand is absent = the gap. Each gap maps to a Next-Step recommendation.

### Step 7. Output

The persona section of the audit doc now has:
1. **Persona summary table** — name, job, confidence, # supporting hooks
2. **Per-persona deep-dives** — using the template above
3. **The competitor cross-reference matrix**
4. **Gaps + Next Steps** — specific to which personas the brand should add hooks for

---

## What this fixes vs. the May 19 Flora audit (v1)

| v1 (the bad approach) | v2 (this methodology) |
|---|---|
| Eyeball ~9 ad cards in a screenshot | Pull 11+ ads from `list_recon_ads`, ranked by days-running |
| Guess 5 personas from creative cues | Derive personas from JTBD job-clusters, minimum 3 hooks per cluster |
| No confidence labels | Every persona gets H/M/L confidence |
| No competitor parallel | Mandatory side-by-side recon matrix |
| No vocabulary | Verbatim hook phrases become persona vocabulary |
| "Foodie / Chef / Family / Gifter / Wellness" — generic | Job-named ("The Real-Italy Seeker", "The Viral Discoverer") — specific |
| No awareness stage mapping | Every hook tagged to a Schwartz stage |
| No validation step | claude-persona AI panel as the validation pass |

---

## AI Panel Prompt Template (Step 5)

When dispatching the panel via Agent tool:

```
You are simulating a panel of [N] potential customers for [brand]. Each panel member
has a distinct persona profile.

For each panel member, I'll give you:
- Their job-to-be-done (functional/emotional/social)
- Their trigger
- Their top pain
- Their awareness stage

Then I'll show you [N] hooks the brand is running. For each hook, score it 1–5 for
each panel member on these dimensions:
1. Would they stop scrolling for this hook? (attention)
2. Would they feel "this is for me"? (resonance)
3. Would they click through? (intent)

Return:
- A score matrix (hooks × panel members × dimension)
- The hook with the strongest unified resonance
- The hook with the most polarized response (some love it, some don't — segmentation signal)
- Any persona who gets NO hooks scoring 3+ across all dimensions (= persona being ignored)

Keep responses concise. Quote the panel member's reasoning verbatim where it's specific.
```

---

## Anti-patterns (red flags — STOP)

| Red flag | Why it's wrong |
|---|---|
| Naming a persona from creative tone alone ("the foodie") | Persona = job, not vibe |
| Counting persona presence with check marks | Count by # of supporting hooks, not yes/no |
| Single-source persona | Per Iron Rule #1 — need 3+ hooks |
| Persona that's just the brand's positioning statement | That's marketing copy, not a customer |
| Recommending lookalike audiences off persona work | Per `feedback_meta_ads_2026` — creative-as-targeting in 2026, not LAL |
| Skipping competitor recon | Personas without competitive context = strategy without map |
