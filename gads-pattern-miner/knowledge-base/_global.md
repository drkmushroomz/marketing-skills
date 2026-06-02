# JF Cross-Account Patterns
_Updated 2026-05-30 — first patterns from Jinx L90D TOF analysis._

This is the cross-account playbook. Patterns get promoted here from per-client KBs after they're observed on 2+ accounts OR when the pattern is fundamentally methodological (applies regardless of account).

---

## TOF / Brand-Awareness Accounts — Best Practices

### Preflight (before touching the account)

1. **Pull HQ `get_client_goals` first.** Sub-goal names reveal the lens: "Store Visits", "Engagement", "Reach", "Pear Conversion", "Branded" → TOF/retail. "Conversion", "ROAS", "CAC" → DTC.
2. **Skim Slack `#<client>` / `#jf-<client>` and Gmail for 30d.** Look for active KPI language: "CPMs creeping up", "view rate", "Tracksuit", "brand recall", "completion rate". These tell you what the team is actually optimizing.
3. **Pass `--kpi-type tof|retail` to `mine.py`** so the run pulls video metrics + branded trend + conv-category breakdown. Default DTC framing will lie to you.

### Don't trust the HQ aggregator alone

HQ showed Jinx Google Ads `last_30d_spend: 0` while the account had spent $194K L90D. The HQ platform-spend integration is broken or stale for some connections. Always cross-check with direct API.

### KPIs that matter on TOF accounts (and the data sources)

| Signal | Source | Interpretation |
|---|---|---|
| **CPM by format** | Google Ads `metrics.average_cpm` by `advertising_channel_type` | Instream typically $0.60–1.00, Shorts $1.60–5.50. Don't average — break out by format. |
| **Video completion Q25 → Q100** | Google Ads `metrics.video_quartile_p25_rate` etc. on `campaign` | Q100 >50% = creative is sticky. Q100 <5% = format-creative mismatch. Q100/Q25 ratio shows hook retention. |
| **Branded organic clicks MoM** | GSC API `query CONTAINS <brand>` | THE TOF lift signal. Uncapped by ad budget. |
| **Branded organic query proliferation** | GSC top-30 branded queries | Long-tail variants (research, intent, product-name) growing = awareness expanding. Head term only = no diffusion. |
| **Conv-category split** | Google Ads `segments.conversion_action_category` | STORE_VISIT vs PURCHASE vs LEAD. Don't roll into one CPA number. |
| **Tracksuit / brand-tracker deltas** | Client-provided | If they have one, this is the ground truth. Paid Google + organic GSC are proxies. |

### Lift analysis methodology

When asked "is TOF working?":

1. Define windows: **pre-spend** (3+ months before TOF ramp), **TOF ramp** (high-spend window), **post-spend** (tapered or off).
2. Pull GSC monthly branded clicks + impressions for the entire window.
3. Compare averages across the three periods.
4. Look for **retention** — if post-TOF branded clicks stay >baseline, real memory effect. If decays fully, paid-driven only.
5. Look for **query proliferation** — sum unique branded queries with >50 impressions/mo across the windows. Growth signals awareness expanding.

Causation caveat is mandatory. Without a control DMA or MMM, lift correlation is not proof. Always state this explicitly.

### Common mistakes to avoid (recurring patterns to check)

- **🚫 Using paid-branded impression volume as a "demand" signal.** Paid branded is budget-capped (often $600–$2,550/mo on JF plans). Use organic GSC, not paid.
- **🚫 Applying CPA/ROAS framing to a TOF account.** Video spend with $0 online conv is not a leak; it's the budget design.
- **🚫 Treating PMAX Store Locator conv as "online" CPA.** Store visits are auto-counted as conversions, polluting account CPA. Segment by `conversion_action_category` before any rollup.
- **🚫 Trusting bare-brand term impressions.** Position >4 → polluted by other entities sharing the name (League of Legends "Jinx," etc.). Filter to brand-plus-modifier.
- **🚫 Rolling CPM across the account.** Hides format-level CPM divergence. Always split video metrics by `advertising_channel_type`.
- **🚫 Treating "missing asset BEST/GOOD/LOW labels" as a creative quality signal.** PMax + Demand Gen accounts don't grade RSAs the way Search-RSA accounts do. Use CTR + completion proxies instead.

### TOF-specific findings to look for on every account

Run this list on each new TOF account. Document the answers in the per-client KB:

1. **Instream vs Shorts CPM gap.** Expect 3–8x difference. If Shorts CPM ≈ Instream CPM, something's off (creative misformatted, audience too narrow).
2. **Q100 completion by campaign.** If best campaign <30% Q100, the creative isn't holding viewers. If best is >50%, fund harder.
3. **Branded organic +/- during TOF window.** If branded clicks dropped during high-spend, TOF creative isn't memorable (or there's a brand-health issue).
4. **Long-tail branded query growth.** If the top-30 branded queries are mostly variants of the head term ("brand X dog food", "brand X reviews", "is brand X good"), TOF is working. If only the head term grows, TOF is just paid-acquired without diffusion.
5. **Branded paid headroom.** With paid-branded budget capped at $X/mo, check Google Ads `metrics.search_impression_share` on branded campaigns. If <80%, you're leaving harvested-awareness conversions on the table.
6. **Retail/Pear/offline attribution path.** Walmart-proximity, store-locator, "near me" queries with 0 online conv — these are working IF the brand has retail distribution and a Pear-style integration. Otherwise they're real waste.

### Channel/format unit economics (rule-of-thumb benchmarks from Jinx L90D)

Use these as starting points, not gospel. Each brand has its own range.

| Format | "Good" CPM | "Good" Q100 | Notes |
|---|---|---|---|
| YouTube Instream (skippable) | $0.60–1.50 | 25–75% | The TOF workhorse for D2C/CPG |
| YouTube Shorts | $1.50–3.00 | 5–15% | Shorter format = lower completion is expected, but <2% is broken |
| Demand Gen — In-Feed | $2.00–4.00 | 8–20% | Mixed surfaces, harder to judge in isolation |
| Demand Gen — Shorts | $1.50–3.00 | 3–10% | Same caveat as YouTube Shorts |
| PMAX Local Store Visits | varies | n/a | Optimize on cost-per-store-visit, not video metrics |

### What to ask the client on the status call

- Do you measure brand recall externally (Tracksuit, Latana, Brand Lift Studies, custom panels)?
- Are there control DMAs / holdout markets to isolate TOF causal lift from distribution lift?
- What's the offline-to-online attribution gap (retail sell-through vs reported online conv)?
- What's the post-TOF decay budget commitment? (If branded organic decays toward baseline after spend stops, the question is whether to defend gains with sustained TOF.)

### Open methodological questions (still being figured out)

- Best window for "lift" comparison — 3mo pre vs 6mo treatment vs 6mo post? Or seasonally aligned YoY?
- How to weight Shorts (low completion, high reach) vs Instream (high completion, lower reach) in a single brand-strength score?
- Whether PMAX Store Visit conversion auto-value of $1 should be tuned (probably yes — affects PMax bidder).
- Optimal cross-account threshold to promote a per-client pattern to this global file (currently informal; default to "seen on 2+ accounts").

---

## TOF Performance Best Practices (lowest CPM, highest engagement, highest-quality impressions)

Grounded in Jinx L90D data + general YouTube/TOF playbook. The Jinx data showed an **8x CPM differential** between best format ($0.63 Instream Cat) and worst ($5.36 Video Shorts) — format and creative decisions move CPMs more than bid tweaks.

### 1. Format selection (the biggest CPM lever)

- **In-Stream Skippable with TARGET_CPM is the TOF workhorse.** $0.60–$1.50 CPM at scale. Jinx's "[Y] - Instream - Cat" hit $0.63 CPM across 25M impressions at 73% Q100.
- **YouTube Shorts as a TOF format is broken until completion is fixed.** Jinx Shorts: $5.36 CPM (8x worse than Instream) and 2.3% Q100. Either the format-creative pairing is wrong, or Shorts is being asked to do a job (TOF) it doesn't do well. Default: don't use Shorts as a TOF workhorse — use it for retarget/CTA, not first-touch awareness.
- **Bumper Ads (6s non-skippable) only as recall reinforcement** after an In-Stream view, never standalone TOF. Use Google's Ad Sequencing to wire In-Stream → Bumper.
- **In-Stream Non-Skippable (15s)** has guaranteed view but 2–4x the CPM. Reserve for high-stakes moments (launch, seasonal push), not always-on.

### 2. Creative that lowers CPM (by driving completion + reducing skip)

- **Brand/hook reveal in first 5 seconds.** Mel/Matthew's 5/29 Dog Math UGC cutdown (12s reveal → faster) is the right instinct — earlier reveal reduces skip rate, which Google reads as quality and rewards with cheaper inventory.
- **Audio-on creative.** ~70% of YouTube views have sound enabled (vs ~15% on Meta). Don't design TOF YouTube creative for silent autoplay.
- **Subtitles for muted-phone viewers.** Most cost-effective creative addition.
- **Aspect ratio coverage.** 16:9 (Instream/desktop YouTube) + 9:16 (Shorts/mobile) + 1:1 (Discover/Gmail/grid placements). Wrong aspect = downgraded placement = higher CPM.
- **Sound-first vs sight-first variants** for A/B. Sound-first generally wins on TOF YouTube.
- **Length test in same campaign:** 15s + 30s + 60s cuts of the same story. 15/30 win on CPM, 60s wins on completion. Pick by goal.

### 3. Audience quality (high-quality impressions, not just cheap ones)

- **Custom Intent built from competitor + category search terms** = highest-intent reach. Slight CPM premium, but impressions actually move branded search downstream.
- **In-Market segments** (e.g. "Pet Food Buyers" for Jinx, "Wine Enthusiasts" for DeLille) deliver intent-grade users at moderate CPM. Default starting tier.
- **Affinity segments** as scale-out only — lower quality, cheap reach. Layer underneath In-Market, not above.
- **First-party Customer Match** for awareness-retargeting recent site visitors. The most engaged audience you have; underused on most JF accounts.
- **Lookalike removal (2026 Meta playbook applies here too)** — Google's "Similar Audiences" is deprecated; rely on Custom Intent + In-Market + Customer Match.

### 4. Pacing & frequency (waste prevention)

- **Frequency cap 3–5 views per user per week** for TOF YouTube. >7 = waste AND drives effective CPM up (the algorithm overpays trying to find the remaining unreached users).
- **Steady daily pacing** beats bursts. YouTube/Demand Gen algorithm learns slowly — sudden budget shifts trigger relearning.
- **Creative rotation every 30–45 days.** Same ad past 60 days = novelty drop + frequency buildup = CPM creep (the "CPMs creeping up" Mel called out on 5/29).
- **Multi-creative-per-week refresh** keeps the algorithm exploring rather than settling on one fatigued variant.

### 5. Placement discipline (the silent CPM killer)

- **Periodic placements audit** (Reports → Ad locations). MFA / bot-network channels can spike cheap garbage impressions that don't contribute. Look for channels with 5–10x normal impression volume per dollar but ~0% engagement.
- **Maintain a JF-wide exclusion list** of low-quality channels across all clients. Build once, apply everywhere.
- **Brand suitability: Standard** is the default sweet spot. "Expanded" gives lower CPM but quality drops. "Limited" inflates CPM with marginal safety benefit.
- **Topic + keyword layering** on YouTube: Topic = "Pets & Animals > Dogs" sets the bucket, Keywords narrow to specific channel/video contexts. Layering reduces wasted impressions, lowers effective CPM by 15–30%.

### 6. Bidding & budget strategy

- **TARGET_CPM for pure reach** (the Jinx Instream Cat workhorse). Google finds cheapest matching inventory.
- **TARGET_CPV (cost-per-view)** for engagement-prioritized campaigns. Charges only on 30s+ views. Different unit economics — forces creative to earn the view.
- **Don't budget-cap branded Search** when `search_impression_share` is <80%. Jinx's `[EXACT] jinx dog food` runs at $1.82 CPA but the branded line is capped at $600/mo per HQ plan — meaning we're leaving harvested TOF demand on the table. **Branded budget should flex up with organic branded growth.**
- **PMax Store Visit conv value should be tuned**, not left at Google's auto-$1. Affects PMax bidder. Calibrate to (avg basket × in-store close rate) for Pear-integrated accounts.

### 7. Sequencing (compounding brand recall)

- **In-Stream 30s story → Bumper 6s reminder.** Google's Ad Sequencing feature. The bumper rehydrates memory of the longer view 1–2 days later.
- **Cross-channel TOF → branded Search → site → retargeting.** Don't audit any leg in isolation. The 36% branded organic lift we found on Jinx is the *compound* of YouTube + Demand Gen + retail distribution + PR — never one channel.

### 8. Engagement signals to watch beyond CPM

- **Q100 completion >50%** = creative is sticky. Fund harder. (Jinx Instream Cat: 73.3%)
- **Q100/Q25 ratio** = hook retention. If Q25 = 25% and Q100 = 5%, you're losing 80% of the people who got past the skip button. Hook is wrong.
- **Earned actions** (subscribes, shares, channel visits from ad). Free secondary impressions. YouTube reports these.
- **View-through conversion rate** in retargeting campaigns. Signal that TOF impressions are remembered.
- **CTR ≠ TOF quality.** A 5% CTR on YouTube can mean intent (good) OR clickbait creative (bad). Cross-check with downstream brand-search lift.

### 9. Format-specific gotchas

- **Demand Gen != YouTube In-Stream.** DG runs across Discover/Gmail/YouTube simultaneously. Useful as a retargeting/scale layer, not as a substitute for In-Stream TOF.
- **PMax Local Store Visit campaigns have their own optimization track** — don't mix into video CPM benchmarking. Optimize on cost-per-store-visit.
- **Asset performance labels** (BEST/GOOD/LOW) only populate well for Search RSAs with high volume. In PMax/DG-heavy TOF accounts, almost everything is PENDING/NOT_APPLICABLE (Jinx: 100% pending/N-A across 1,432 assets). Use CTR + completion proxies for creative judgment.

### 10. The 80/20 of TOF CPM (Jinx-specific findings)

If Edwin had 30 minutes to improve Jinx's L90D CPM without changing creative:

1. **Cut budget on YouTube Shorts variants with <5% Q100** (frees ~$50K/quarter) and redeploy to Instream Cat.
2. **Move Demand Gen Shorts spend into Instream Skippable** — 3x cheaper CPM, 30x higher completion.
3. **Uncap branded Search budget** to capture the +36% organic branded lift this skill identified.
4. **Tune PMax Store Visit conv value** from auto-$1 to actual (probably $3–8 per incremental visit).
5. **Add frequency caps to YouTube campaigns** (any campaign without them is overpaying for tail users).

---

## Methodological best practices (account-agnostic)

These apply to any client work, but were forced into focus by the Jinx exercise:

- **Always declare the KPI lens at the top of the per-client KB** before listing winners/losers.
- **Never read raw JSON dumps into model context** when there's a Python aggregation layer available. The Jinx raw GSC file is 700KB; the aggregated summary is 5KB. Same insight, 100x cheaper.
- **Pre-aggregate at SQL/script level** — `WHERE impressions > N`, `status != REMOVED`, top-N ordering. Filter at source, not in context.
- **Pull comms context before pattern-mining.** What the team is actively testing (Slack threads, Gmail action items) shapes which patterns matter. Edwin caught the TOF-lens issue immediately because he reads the comms; the data alone was ambiguous.
- **Save corrections to memory immediately** when called out. Otherwise the next account gets the same mistake.

---

## Negative-Keyword Research — Default Methodology

Forced into focus by the Cat Years build (2026-06-01). First attempt was a gap analysis vs Jinx/ZipLineGear — surfaced only 18 candidates of mostly account-specific noise. Edwin called it shallow. Switching to **Ahrefs deep-mine across multiple KW root clusters** surfaced 41+ high-impact candidates blocking ~55,000+ off-intent searches/mo. Across all rounds, Cat Years went from 57 → 158 negatives in one session.

### What NOT to do (the trap I fell into)
- **Don't default to gap analysis vs mature accounts.** ZLG's "diy zipline" or Jinx's "homemade dog food" don't transfer. Mature-account negatives are 80%+ harvested account-specific noise from Search Term reports. They're complementary, not primary.

### What TO do (proactive deep-mine for any new account)

1. **Pull the PPC keyword targets** from the campaign spec.
2. **Run 4-6 Ahrefs `keywords-explorer-matching-terms` calls** across these root types:
   - **Primary roots** from your PPC list (e.g., "cat hydration", "cat dehydration")
   - **Category broad** (e.g., "cat treats")
   - **Adjacent broad** (e.g., "cat health", "cat sick", "kitten" / "puppy")
   - **Brand name itself** — critical for catching brand collisions (Cat Years = unit of cat age AND Maggie Rogers song; Jinx = League of Legends character)
   - **The offer keyword** ("free sample", "free trial") — catches non-vertical freebie seekers (cannabis/Viagra/template/insurance)
   - **Questions mode** (`terms="questions"`) on primary roots for "how to X" / "why does X" patterns
3. **For each call:** `select=keyword,volume,intents,cpc,parent_topic`, `match_mode=terms`, `where={"field":"volume","is":["gte",100]}`, `order_by=volume:desc`, `limit=50-100`.
4. **Categorize results into clusters:**
   - Informational patterns ("how to X", "why does X", "what is X")
   - Adjacent product categories (calming/dental/CBD/freeze-dried/GPS/insurance)
   - Competitor brands NOT being bid on
   - Non-vertical free-sample noise (cannabis/Viagra/templates)
   - Brand collisions (other meanings of the brand name)
   - Vet emergency / terminal / recall
   - Foreign language
   - News / Discord / coloring / entertainment
5. **Consolidate broad-first.** A few BROAD negatives blocking a cluster > many narrow PHRASE variants. Use PHRASE only where BROAD would over-block protected keywords.
6. **Check conflicts BEFORE adding.** Don't BROAD-negate a competitor brand you're conquesting via "X alternative" exact-match.
7. **Estimate volume blocked per cluster** — helps prioritize and communicate impact to client.
8. **Present in a sheet for review:** columns `# | Keyword | Match Type | Category | Volume/Rationale | Risk | Approve (Y/N/M)`. Yellow Approve column.
9. **Push via idempotent script:** read existing SharedSet, add only what's new. Pattern: `scripts/gads_<client>_negatives_<version>_push.py`.

### Default not-to-broad-negate list
- `dying`, `sick cat`, `lifespan`, `life expectancy` — worried-pet-parent might be exactly the customer
- `vs`, `near me` — own brand defense / purchase intent
- Brand names you ARE conquesting (broad-negate kills your own targets)

### Volume-blocked benchmark
For a new D2C account with ~10 PPC keywords, expect 100-200 high-confidence negatives across 8-10 clusters, blocking 50-80K off-intent searches/mo. Cat Years hit 158 (57 v1 + 42 v2 broad-first gap + 18 v3 Ahrefs + 41 v4 deep-mined).

### Tools required
- Ahrefs MCP: `keywords-explorer-matching-terms`
- Google Workspace MCP: `create_sheet`, `modify_sheet_values` (for review tab)
- Google Ads API direct (via `scripts/gads_tokens.json`): `SharedCriterionService` for push
