# Jinx — Google Ads Pattern Notebook
_Last mined: 2026-05-30 (L90D, 2026-03-01 to 2026-05-30)_
_Account: 5841094176 (MCC: 1874174744) | Spend L90D: $194,697_

## Account framing
- **KPI lens:** TOF / brand awareness + retail / omnichannel (Pear Commerce integration drives store visits at Walmart). Not DTC-ROAS.
- **Primary metrics:** CPM, video completion (Q25→Q100), branded-search monthly lift, store-visit cost, reach/frequency. Tracksuit referenced in 5/20 status call action items as the brand-tracking source of truth.
- **Source:** HQ `get_client_goals` (Apr–Oct 2025 monthly plans), Slack `#jinx`/`#jf-jinx` (creative tests, CPM watch, Tracksuit references), Gmail (Pear Commerce catalog ads integration thread w/ Dino, May 27–28).
- **Account-level conv categories:** Google Ads is recording **STORE_VISIT only**. No PURCHASE category. Online purchase attribution is intentionally not in this account — Pear handles the retail bridge.
- **What "leak" means here:** broad-match waste in the small Search Prospecting budget; rising CPM with no branded-search lift; falling video completion rates. NOT YouTube spend without online conv (that's the budget design).

## Confirmed TOF/retail signals

- **Instream video is the workhorse format.** `[JF] - [AW] - [Y] - [PR] - Instream - Cat -*` (the largest VIDEO campaign) ran 25.4M impr at **$0.63 CPM and 73.3% Q100 completion**. A second Instream campaign hit $0.64 CPM / 29.2% Q100. **In-stream is the format that's earning brand recall budget.** [2026-05-30]
- **Walmart-proximity terms are firing as intended.** `walmart near me`, `walmart dog food`, `dog food at walmart` pull 26–42% CTR with 0 online conv recorded — and 0 is the right number, because the conv pathway is in-store via Pear, not online. CTR is the right metric here, and it's strong. [2026-05-30]
- **Branded paid search at sub-$5 CPA is incremental brand-demand capture.** `[EXACT] jinx dog food` 1,498 conv / $2,723; `jinx` Exact 200 conv / $239. With branded budget capped at $600–$2,550/mo in monthly plans, this is the funnel-bottom catchment — efficient by design. Headroom check: is impression share capped? Worth monitoring. [2026-05-30]
- **Celebrity-cofounder query overlap is unusually efficient.** `chris evans pet food` 29 conv at $79 ($2.72 CPA); `chris evans dog food` 30 conv at $182 ($6.07 CPA). These are warm-prospect queries — the TOF investment is converting curiosity → branded recall → search. Likely worth carving into its own ad group with celebrity-forward creative. [2026-05-30]

## Confirmed TOF/retail concerns

- **🚩 Branded search volume is flat MoM.** L90D branded-term (`%jinx%`) trend:
  - Mar 2026: 17,419 impr / 2,848 clicks
  - Apr 2026: 14,605 impr / 2,380 clicks  (-16% MoM impr)
  - May 2026: 15,714 impr / 2,597 clicks  (+8% from Apr, still below Mar)
  For an account spending $113K+/mo on YouTube TOF, the expected signal is *rising* branded query volume over time. We're not seeing it. Two questions for the team: (1) is this seasonality (need YoY)? (2) is the YouTube creative pulling enough memory hold to move people from "saw the ad" → "searched 'jinx dog food'"? Cross-check against Tracksuit deltas. [2026-05-30]
- **🚩 YouTube Shorts is dramatically underperforming Instream.** Across L90D:
  - **Instream Cat**: $0.63–0.64 CPM, **29–73% Q100 completion**, 25M+ impressions
  - **Shorts (mixed Video + Demand Gen)**: $1.60–$5.36 CPM, **0.2–2.4% Q100 completion**
  Almost nobody watches Jinx Shorts to completion. The 5/29 internal test (Matthew/Mel "Dog Math UGC cutdown — 12s vs 22s reveal" → testing as TOF) is the right instinct: shorten the hook, get Jinx visible earlier. This data backs it up. [2026-05-30]
- **🚩 CPM creep flagged by team is real but format-specific.** The 5/29 Slack note about "CPMs creeping up" lines up with the Shorts pattern above — Shorts CPM is 3–8x the Instream rate. The creep is concentrated in short-form Demand Gen, not the workhorse Instream lines. [2026-05-30]
- **Genuine waste exists in the small Search Prospecting budget.** Even on a TOF account, the Search Prospecting line ($2,550–$2,552/mo plan target) is bleeding on broad-match category terms:
  - `[BROAD] cat food` → $3,707, 4,274 clicks, 0 conv (any category)
  - `[BROAD] Fresh Dog Food` → $2,834, 0 conv
  - `[BROAD] Premium Dog Food` → $821, 0 conv
  Total identifiable broad-category waste ~$8.5K L90D / ~$2.8K per month — that's ~quarter of the entire Search Prospecting monthly budget. Easy fix: tighter match types or aggressive negatives. [2026-05-30]

## Open questions (for next status call / Wed huddle)

- **Tracksuit-to-branded-search correlation.** When Tracksuit unaided awareness lifts, does branded paid-search impression volume lift in parallel? If yes, branded volume is a real-time TOF KPI we can mine here. If no, we need to recalibrate which signal we trust.
- **Pear Commerce catalog ads error** (Mel ↔ Dino thread, May 27–28). Open issue. Doesn't appear in Google Ads data here but could be muting some store-visit attribution. Mel collected screenshots 5/28 — waiting on Dino.
- **STORE_VISIT value calibration.** Google is auto-valuing each store visit at exactly $1 (4.6M conv → $4.6M value). If we tune the conv value to actual avg basket × in-store close rate, the optimization algorithm in PMax may shift behavior. Worth a conversation.
- **YoY branded search comparison** — need L90D 2026 vs L90D 2025 to know if "flat" is actually a decline disguised as seasonality.
- **Asset-level grading.** 1,432 ad assets tracked, 0% graded BEST/GOOD/LOW. Search RSAs aren't accumulating enough volume to grade (Search is 7% of total spend). Not actionable from this skill — but worth noting we cannot mine creative winners at the asset-rating level in this account. Have to grade creative manually from CTR / completion proxies instead.

## GSC organic lift analysis (2026-05-30, updated with direct GSC API)

**Data source:** Direct Search Console API via marketing@ ADC (`sc-domain:thinkjinx.com`, `siteFullUser` access). The earlier Ahrefs-GSC analysis was incomplete — Ahrefs sync stopped Jun 2025, so I missed the bulk of the TOF window. Direct GSC has the full 17-month window.

### Branded organic monthly trend (queries CONTAINS "jinx")

| Period | Paid TOF plan (HQ) | Branded clicks/mo avg | Branded impr/mo avg |
|---|---|---|---|
| **Pre-TOF** (Jan–Mar 2025) | — | 2,828 | 238K |
| **TOF ramp** (Apr–Sep 2025) | $83K–$141K/mo | **3,857 (+36%)** | **385K (+62%)** |
| **Post-TOF** (Oct 2025–May 2026) | $47K Oct, undocumented after | 3,479 (+23% vs base) | 277K (+16% vs base) |

### Key findings

- **TOF lift is real and measurable** in branded organic clicks. +36% during high-spend window vs baseline.
- **Partial retention post-spend.** Even 7 months after TOF spend tapered, branded clicks are still +23% above baseline. Consistent with brand-recall investments having residual effect, not pure paid-decay.
- **Long-tail branded expansion** — top 30 branded queries are mostly research/intent variants (`is jinx dog food vet approved`, `who makes jinx dog food`, `chris evans jinx`, `jinx kibble sauce`, `jinx careers`, `jinx dog food recall`). Only 2 head terms. When awareness grows, queries proliferate — that's the TOF signature.
- **Branded share of total site impressions DECLINED** (Jan 2025: 20.5% → 2026-Q1: ~5–10%) — but this is because total site traffic 4x'd faster than branded grew. Total non-branded organic is being pulled by content/SEO work; branded grew on a slower absolute trajectory.

### Causation caveat

Correlation, not proof. Branded growth could come from any/all:
- Paid TOF (YouTube In-Stream, Demand Gen)
- Walmart distribution expansion → retail availability triggers searches
- Chris Evans co-founder content (queries like `chris evans jinx` are top-30)
- PR / earned media moments
- Content publishing → branded query discovery

The data is *consistent* with TOF being effective. Without a control DMA or MMM, can't isolate paid TOF's specific share. But this is no longer evidence *against* TOF working.

### Earlier-turn correction

The prior turn claimed branded was "flat MoM" based on Google Ads paid impressions (16K/mo). That was misleading — paid branded is budget-capped at $600–$2,550/mo per HQ plans. Organic GSC, uncapped, shows real branded demand is up meaningfully. **Reading a budget ceiling as a demand signal was the mistake.**

### Open follow-ups for the 6/10 status call

1. **Tracksuit unaided awareness deltas** — do they track the branded-organic lift? (Caitlin sending per 5/20 action items.)
2. **Geo-level analysis** — branded growth in Walmart-distribution DMAs vs control areas. Decomposes TOF lift from distribution lift.
3. **MMM if budget allows** — proper attribution to isolate paid contribution.
4. **YoY 2024 baseline** — GSC API caps at 16 months, so pre-2025 baseline isn't retrievable from this source. Could request from Jinx if they have older exports.

## Active tests in flight (from comms)

- **Dog Math UGC cutdown (12s reveal vs 22s reveal).** Launched 5/29 as TOF test. Hypothesis: shorter intro pulls CPM down while holding CTR. Next mining run should compare CPM/completion of the cutdown ad vs the original.
- **N-Gram Negatives — JINX** scheduled cron at 9:17 AM weekly (last run 5/18). Already harvesting search-term waste — confirm the cron is catching the broad cat-food terms above.

## Test inventory

- Active campaigns: 116 (L90D, status != REMOVED)
- Spend split: Video/DemandGen ~$113K, PMAX ~$60K (Local Store Visits dominant), Search ~$13K (Branded + Prospecting)
- Conv categories tracked: STORE_VISIT only
- Branded-search baseline: ~16K monthly impr, ~2,600 monthly clicks

## Mining log

| Date | Window | Spend | KPI lens | Notes |
|---|---|---|---|---|
| 2026-05-30 | L90D | $194,697 | TOF + retail | First run. Branded MoM flat. Instream >> Shorts. Store-visit-only conv tracking. View-rate query bug — re-investigate next run. |
