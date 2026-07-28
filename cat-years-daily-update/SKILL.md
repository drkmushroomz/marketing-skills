---
name: cat-years-daily-update
description: Daily cron internal update on cohort 2 (freebie-excluded) post sample delivery, written as a CEO-level state-of-affairs the way Edwin opens the client call - momentum first, sample sizes on every number, a plain read of where it's going. Carries a front-of-funnel creative + awareness/TOF read at the insight-writer bar (winning line + DNA + persona/awareness-stage + next test, WoW-led) alongside the back-of-funnel email/buyer math. Reads pre-collected facts + the client-questions ledger, pulls fresh Klaviyo delivery/flow numbers + HQ creative/campaign/retargeting + yesterday's client-channel messages, writes the Slack report file. The wrapper posts it to #cat-years for team QA.
---

# Cat Years Cohort-2 Daily Update (CEO-level state of affairs)

ClickUp 86bavdc4p. The wrapper `scripts/cat_years_daily_update.ps1` already ran
`cy_daily_update_facts.py --collect`, so the cohort math (recipients, freebie
splits, buyers, cohort-1 same-age baseline, GA4 email-return proxy, data-health
flags) is at `scripts/_cy_daily_update_facts.json`.

**Model this on how Edwin opens the status call** (his "lay of the land"): he
leads with direction and momentum for cohort 2 with freebie stripped, walks the
improved funnel in order (creative + awareness/TOF that feeds it -> purchase
intent -> email flow -> Shopify funnel), then gives the honest hard-conversion
picture with sample sizes and a plain "here's where this is going" read. This
update is that same story, daily, for the internal team. It is NOT a metric dump.

The front of the funnel (which creative wins and why, what the awareness/TOF
spend is doing) gets a first-class read here. Edwin flagged 7/17 that the
creative/awareness/TOF notes were thin, so Step 4.5 carries that read at the same
bar as the weekly insight-writer, distilled for the daily.

Your job: **read facts + the client-questions ledger -> pull the live numbers
(Klaviyo delivered series + flow reports, HQ retargeting) -> scan yesterday's
client-channel messages -> compose the state-of-affairs -> Write it to
`scripts/_cy_daily_update_report.txt` -> update the ledger -> stop.** The
wrapper posts the file. Do NOT post to Slack yourself.

## Hard rules

- NO em dashes anywhere (Edwin hard rule). Commas/periods only.
- EVERY number carries its sample size (n). Jordan asked for this explicitly on
  the 7/16 call: "when you send over the data, can you also provide the n". A
  rate with no n is a failure.
- Never fabricate or carry forward a number. If a pull FAILS, say "unavailable
  today (klaviyo/hq error)" next to that line. Never reuse yesterday's figure.
- NEVER infer a system is off from a failed pull. A Klaviyo error means we
  could not read it, not that flows stopped or samples did not deliver. (This
  exact mistake shipped a wrong post on 7/17.)
- Complete days only: the window ends at `facts.yesterday`.
- Freebie is excluded from every cohort-2 number, always. State it once.

## Step 0 - Load the analyst playbook (self-improvement loop)

`Read .claude/clients/cat-years/learnings.md` and find the "Daily-update analyst
playbook" section (recipes P1..Pn). APPLY EVERY recipe this run: new-vs-recurring
split, discount-depth, sampler-vs-direct, AOV composition, maturity gate,
find-new-not-parrot, de-aify cadence, and the front-of-funnel creative +
awareness/TOF read (P8, the read Edwin flagged thin; it drives Step 4.5). The
playbook is how this update compounds; treat every recipe as required doctrine.

## Step 1 - Read the facts

`Read scripts/_cy_daily_update_facts.json`. Everything below refers to its keys.
Note `facts.data_health`: if `orders_export_current` is false, the buyer count
is stale to `orders_export_last_buy` and UNDERCOUNTS recent buys, flag it on the
buyers line ("orders export stale to {date}, undercounts recent"). If
`klaviyo_fields_stale` is true, prefer your own live pulls below.

## Step 2 - In-hand deliveries (Klaviyo Ud2PPs, live)

Call `mcp__klaviyo__query_metric_aggregates`:
- `metric_id: "Ud2PPs"` (Mail piece received, the reliable delivered feed)
- `measurements: ["count"]`, `interval: "day"`, `timezone: "America/New_York"`
- `filter: ["greater-or-equal(datetime,<c2_delivery_series_start>T00:00:00)", "less-than(datetime,<facts.today +1d>T00:00:00)"]`

Deliveries from Jul 7 on are cohort 2 (cohort 1 flat at its 7,638 baseline).
Compute `c2_in_hand` = sum through `facts.yesterday`, `yesterday_delta` = the
count on `facts.yesterday`. Deliveries DO register now (the feed started firing
~7/10); report the actual number. Fallback on error: use
`c2.delivered_per_metrics_json` and append "(carried from last dashboard
refresh, klaviyo unavailable)". Do NOT claim samples have not arrived.

## Step 2.5 - Cohort-2 buyers (fresh Shopify pull, supersedes stale facts)

`facts.c2.buyers_since_ship` is computed by python from `.claude/_cy_orders_full.json`,
which is refreshed by the 7am dashboard job and CAN BE STALE (it was a week
behind on 7/17, reporting 0 cohort-2 buyers falsely). So pull orders fresh here.

Call `mcp__claude_ai_Shopify__graphql_query`:
`{ orders(first:100, query:"created_at:>=2026-07-06", sortKey:CREATED_AT){ pageInfo{hasNextPage endCursor} nodes{ name createdAt email test cancelledAt displayFinancialStatus totalPriceSet{shopMoney{amount}} } } }`
Paginate on `hasNextPage` with `after:endCursor`. Drop test, cancelledAt not
null, displayFinancialStatus REFUNDED, and internal emails (@catyears.com,
@byhandbook.com, jordankfr@gmail.com). Lowercase each email and match against
the cohort-2 recipient list in `scripts/_cy_strata_batch2_export_with_emails.csv`
(column `email`). Count of unique matched emails = cohort-2 buyers; split each
by its `segment_mix_exact` segment via the export's zip. This is the number for
the buyers line, with its n.

If Shopify errors: fall back to `facts.c2.buyers_since_ship.n` and append
"(orders export stale to {facts.data_health.orders_export_last_buy}, likely
undercounts)". Never assert 0 buyers from a failed or stale pull.

## Step 3 - Email flow health, cohort 2 vs cohort 1 same-age

Call `mcp__klaviyo__get_flow_report` twice, once per window
(`skill_inputs.flow_window_c2`, then `flow_window_c1`):
- `conversion_metric_id: "UzD6xZ"`, `filters: 'equals(send_channel,"email")'`
- `statistics: ["recipients","delivered","opens_unique","open_rate","clicks_unique","click_rate","conversions"]`
- `group_by: ["flow_id","flow_name"]`, `timeframe: {"start":"<w0>T00:00:00","end":"<w1>T23:59:59"}`

Keep the two post-sample flows in `skill_inputs.postsample_flow_names` from the
`flow_aggregation` block. Per window compute delivered-weighted open + click
rate and total unique clicks, WITH the recipient n. The flow triggers on
delivery, so the July window is the cohort-2 proxy.

Frame it the way Edwin does: the flow is healthy vs the 1% click benchmark, and
we want 2%. Report cohort-2 rate vs cohort-1 same-age, and vs the old flow
iteration if `facts` carries it. A flow genuinely ABSENT from the window (and
Step-2 shows real deliveries) = "no post-sample sends landed in-window yet".
But if the CALL ERRORS: "flow numbers unavailable today (klaviyo error)" and
say nothing about whether flows fired.

## Step 4 - Retargeting (what's-next input)

If HQ tools aren't visible, call `mcp__claude_ai_jetfuel_hq__load_ads_tools`
(or the `mcp__jetfuel-hq__` twin), then `campaigns_performance` with
`client: "Cat Years"`, dates = the c2 flow window,
`name_contains: "samplerecipients_rt"`, `metrics: ["spend","conversions"]`. Sum
spend + conversions (n). RT targets ALL sample recipients; label it that way.
CAC = spend/conversions only when conversions > 0. Fallback: "rt unavailable
today (hq error)".

## Step 4.5 - Creative + awareness/TOF read (front of the funnel)

This is the read Edwin flagged as thin. The daily update carries a real creative
and awareness note at the Jinx bar, the same way it already carries the
back-of-funnel email and buyer math. Canonical doctrine (do NOT read every run, the budget is tight;
these are the SOURCE of the distilled rules below, read them if a rule is unclear
or when reworking this step): the insight-writer creative-strategist + awareness
system at `~/.claude/skills/insight-writer/references/insight-voice.md` (sections
"Creative analysis depth", "The top-tier bar", awareness-as-first-class), and the
Cat Years creative model + campaign taxonomy at
`~/.claude/skills/insight-writer/clients/cat-years.md`. The DEEP weekly treatment
(watch-time seconds, CPV, organic-vs-paid, the hero audience split-test, the
four-verdict awareness block) is the Friday `/insight-writer cat-years` job. The
daily job is the 1-2 creative/awareness notes that actually MOVED in the trailing
7 days, each carrying a number and a move.

HQ ads tools are already loaded from Step 4. Pull on a TRAILING-7-DAY window
ending `facts.yesterday` (daily creative deltas are noise, so read the week):

1. `campaigns_performance` client "Cat Years", `compare_to: "previous_period"`,
   metrics `["spend","impressions","clicks","ctr","conversions"]`, the 7d window.
   Group campaigns into the three objectives by name:
   - hero/awareness = name has "Drinking Problem", "hero", "tof-awareness", or
     "herovideo" (Meta `jf_tof-awareness_..._herovideo`, plus the TikTok/Google
     hero and the Meta traffic warmup video).
   - sample/MOF = "mof-sample" / "asc" / warmup (Meta `jf_mof-sample_..._asc`).
   - purchase/RT = "samplerecipients_rt".
   Compute per-objective WoW spend + CTR, and the budget-concentration read: what
   share of spend pools in awareness (at ~0 counted samples by design, learnings
   17) versus the converting sample campaigns that carry the clicks. HQ
   `conversions` is BROKEN for Cat Years (0 on every Meta/TikTok row, only Google
   search rows ever show one); never compute CAC/CVR/harvest from it here.
   Verified 7/17 headless test.
2. `top_creatives` client "Cat Years", the 7d window, sorted by spend, then
   `ads_performance` (`platform_type: "meta"`, `min_spend: 1`) for the winner's and
   the bottom performer's copy + poster. `top_creatives` returns Meta ad-level
   `hook_rate`, `hold_rate`, `thruplay_rate`, `completion_rate` AND an `ai_metadata`
   block (hook_text, hook_type, full transcript, claim tags, cta_type, format) that
   is the richest DNA source you have. READ the `full_transcript` and map the
   retention shape (hook/hold/thruplay/completion) onto its beats; that is how you
   build the consumer WHY (see the WHY rule in the discipline below), not from the
   rates alone. Two footguns
   confirmed in the 7/17 test:
   - `top_creatives` returns `ctr` as a FRACTION (0.0009 = 0.09%); `ads_performance`
     and `campaigns_performance` return it as a PERCENT (0.09). Convert before any
     cross-tool math or a comparison line.
   - Creative-level HQ data is META-ONLY. Google ad-level is not synced and TikTok
     is not merged into these calls, so the DNA read is Meta hero/static only; the
     TikTok and Google hero read comes from their campaign rows in step 1 (spend,
     CTR, WoW), not a creative decomposition.
   Respect a min-spend floor (~$100 trailing-7d); a creative under it is
   preliminary, say so. Roll a concept's instances into ONE CTR (total clicks /
   total impressions across instances), never a range. `ads_performance` returns
   one row PER instance, so you roll them up yourself.
   SELECT THE CREATIVE WINNER FROM THE CONVERTING LINE, not account-wide spend rank.
   When awareness owns ~90% of spend (the common case), sorting by spend puts the
   HERO on top, and the guardrails forbid reading the hero on CTR, so a raw
   spend-sort winner is a trap. Filter to the sample/MOF + RT campaigns (or to
   static/UGC sample creatives) and crown the winner THERE. The hero belongs in the
   awareness/tof line, judged on hold, never quoted as the "creative winner" on CTR.
3. Fallback: if `top_creatives`/`ads_performance` errors or is thin, degrade to
   the campaign-level CTR move and write "creative-level read unavailable today
   (hq error)". Never fabricate a winner or carry yesterday's.

PULLED-BACK-WEEK BRANCH (hit in the 7/17 test, it is a NORMAL state, not an error):
when the sample ASC, the leads ASC, the traffic warmup, and the Meta RT all sat at
$0 for the window (turned off, prior-week spend present), there is NO converting
line running and NO sample-static winner to quote. Do not leave a blank `{ctr2}` or
invent a sample CTR. The honest read that week is: hero is holding on TikTok/Meta at
its usual cheap reach, the converting line is dark, and the move is to re-fund the
sample ASC before the next cohort lands (spelling is "re-fund", never "refund").
The creative line becomes "no sample static ran this week, hero video was all the
Meta spend; ad10/the ugc got $0" plus whatever hero-cut test is live. This is a
valid terminal state; write it plainly.

Read it with the SHIPPED-JINX-REPORT discipline. This is the bar Edwin holds these
two lines to (calibrated 7/18 against the real artifacts: `.claude/_kim_jinx_monthly.html`
and the insight-format standard doc `1TK04gk5GwF3xvuE9Zs5jDlhav_dqcHi2NIjB4be1ttU`).
A metric recital fails. What separates the shipped Jinx read from a recital: every
number is paired with its goal AND a plain-language outcome, every move that went
the wrong way carries a MECHANISM, and every read ends in a clean single-variable
next test. Apply that here.

- THE "WHY" MUST BE A CONSUMER MECHANISM, never a metric restatement or an ad
  description (Edwin 7/18: "meta hero held 44%, why is it finishing?"). Two answers
  that FAIL: "held 44%, so half finish" (restates the number) and "front-loads the
  misconception hook" (describes the ad). The real insight is what the message does
  to the VIEWER that makes them stay, click, or drop: the curiosity gap it opens,
  the self-recognition it triggers ("my cat does that"), the worry for their own pet
  it raises, the objection it answers, the proof the stayers were waiting for. To
  build that why, USE the asset you already pulled, do not reason from the numbers
  alone:
  1. Read `ai_metadata.full_transcript` + `hook_text`: what does the video literally
     SAY, beat by beat (the open, the turn, the proof, the CTA)?
  2. Map the retention SHAPE onto those beats: hook% (3s) then hold% then thruplay%
     then completion%. The biggest drop names which BEAT lost people; survival to
     the end names what the stayers came for. The full p25/p50/p75/p100 quartile
     curve is on the Meta MCP `ads_get_ad_entities` (account 2459439407861972,
     cat-years.md hook/completion note); the HQ retention rates plus the transcript
     are enough for the daily, pull the Meta curve only when the why hinges on
     exactly where the drop sits. CAVEAT: HQ `hook_rate` (3s plays / impr) and
     `hold_rate` are NOT on the same denominator, so hold can read higher than hook
     without that being real; never compute a "share of hookers who survived" from
     the two rates or write "holds higher than it hooks". Use them as directional
     shape and compare each rate across cuts (60s hold vs 30s hold); pull the
     quartile curve if you need a true survival ratio.
  3. Infer the consumer reason AT that beat, tied to a persona and awareness stage.
     The bar for "why is the hero finishing at 44%": "the 'your cat has a drinking
     problem' open reframes something owners take for granted, they assume the bowl
     is enough, so it opens a worry loop; the ~44% who hold are the ones it landed
     on, and they sit through the vet-science middle because they now need to know if
     their own cat is at risk and what fixes it. the 30s cut holds 27% because it
     drops that proof middle, so the worry never gets paid off." That names the
     mechanism (worry loop opened, proof pays it off) and who stays (the concerned
     owner who accepts the problem). "holds 44% so half finish" does not.
  Honesty guard: if you cannot ground the why in the asset (no transcript, flat
  retention, or you did not read it), say what read would answer it (the quartile
  curve, a session pull), do not invent a psychological just-so story. A guessed why
  dressed as a finding is worse than naming the gap.
- AWARENESS/TOF MUST READ AS STRATEGY, never a metric list (Edwin 7/6 and 7/18).
  The line to KILL: "hero is 92% of $1,409 at 0.5% ctr / 42% hold, move: re-fund
  the asc" - it lists numbers and stops, opens on a spend stat, and the move names
  no variable. Every awareness number resolves the Jinx way, in this order:
  1. metric vs its benchmark, side by side (hero hold vs the ~47% it held at launch
     and the ~74% 3s-hook; CPM vs target; ctr vs prior wk), never a bare number.
  2. the plain-language outcome (what the number BUYS): "holds ~47%, so about half
     of everyone who starts the video watches it through, which is the awareness
     doing its job at cheap reach".
  3. a MECHANISM whenever a number moved (the Jinx move: "female-only spend dropped
     $1k to $400, CPM fell $2.62 to $1.80, a direct concentration relationship").
     Give the cause, not just the delta. If we pulled hero spend ON PURPOSE, say it
     is intended and read the quality metric that improved (the Jinx "quality-first
     restructure" reframe: a down metric that is the strategy working, not a miss).
     When the moved number is a BLENDED average (hero hold across cuts, blended
     CPM), decompose before attributing: did the per-asset metric actually move
     (real fatigue on the 60s master), or did the MIX shift toward a shallower asset
     (more 30s cut in the blend)? Check the master's own WoW hold before calling a
     blended-hold slip fatigue; a mix-shift artifact and real fatigue need different
     moves. Same trap as the efficiency-blend rule.
  4. the decision names an isolated variable AND a read window: "re-fund the sample
     asc at ~$Xk for the cohort-3 send, judged on sample-CPL vs the $7 target over
     ~5 days" beats "re-fund the sample asc". Source the dollars (learnings, media
     plan); never a bare "+$X".
  Judge the hero on hold + downstream harvest, never CTR. The harvest (did awareness
  produce sign-ups) is ~30% dark in HQ (learnings 19); defer that piece to the Friday
  GA4 deck and carry the concentration + hold-mechanism read here.
- CREATIVE read at the shipped-Jinx bar. A winner is FIVE things, not two:
  1. name the concept AND quote the actual hook line ("a hydrated cat is a healthy
     cat"), and name it as a reusable test unit so it carries forward week to week
     (Jinx does this: "Van Dog concept validated").
  2. the proof metric: rolled-up CTR + hook/hold, each vs the account benchmark
     (sample avg 8.29%, hero 3s-hook ~74% / hold ~47%).
  3. DNA decomposed to the BEAT, not a tag list: the hook TYPE (misconception /
     question / curiosity / problem-stat / claim-and-proof), the narrative arc, the
     TIMING beat ("product in the first 3s", "Jinx intro by 3s"), and the payoff
     ("ends on the cat drinking / the bowl licked clean"). "vet/science claim,
     moving-water bg" is the start; add the arc, the timing, and the payoff.
  4. the persona + Schwartz awareness-stage inference, WHO responds and WHY: "the
     click is the Pet-First Health Seeker who already accepts the problem and wants
     proof, so claim-and-proof wins the sample click while problem-led wins TOF by
     making the unaware aware". Personas live in cat-years.md.
  5. winner vs loser on ONE isolated variable ("ad10 leads because the proof claim
     lands in the first 3s; ad01 fell to 5.9% because the problem-stat hook makes
     the already-aware wait"), and flag any SURPRISE as a signal ("a polished vet
     static is holding where UGC usually wins, worth a look"). The single-variable
     contrast IS the insight and converts straight into the next test.
  Next test = one controlled change + a named baseline + a read window ("brief a
  claim-and-proof UGC variation of ad10's beat, judged on sample-to-purchase not
  CTR, read ~2wk" / "30s hero cut vs the 60s master on thruplay at matched spend,
  read ~5d"). Decompose the loser the same way so the team knows which beat to drop.
- These two lines carry the most SUBSTANCE (Edwin 7/18 wants the real read: number
  vs benchmark, the mechanism when it moved, the persona/DNA, one next test), but
  say it in ONE tight sentence each now, not 2-3 (Edwin 7/22: updates were too long,
  cut ~75%). Keep every element, cut the words; deepest secondary detail goes to a
  thread. They still take the daily voice (lowercase, plain dashes, no labels/bold)
  and the de-aify cadence pass, and the awareness line NEVER opens on a raw spend stat.
- Guardrails (cat-years.md, enforce every run): statics carry ~90% of leads, never
  recommend retiring them (shift the mix with a floor, do not cut); the hero gets
  variations, never new concepts; do not say "scale ad10", it monopolizes the ASC
  and starves the UGC test, so the move is to isolate the underspenders; no
  cross-funnel creative move without a live campaign for that stage (frame it as an
  insight, not an action); watch lead quality on any deal-led or sample-first hook
  and judge it on downstream purchase, not CTR/CPS.
- Mechanical-cause-first: rule out an account/campaign off, a budget cap, or the
  TikTok restriction (dark since 6/16) before reading a WoW creative swing as a
  consumer signal. If a channel went dark mid-window, read before-vs-now
  (active-vs-active, exclude the dark stretch), never the naive straddling WoW.
- FIND NEW (playbook P6): if creative and awareness did not move since yesterday's
  post, collapse to ONE plain "held" line, do not re-read the same winner at length.

## Step 5 - Client questions and campaign movement (ledger)

`Read scripts/cy_client_questions.json` (standing client concerns: status,
next, state, due). Then pull yesterday's messages from both channels via
`mcp__slack__conversations_history` `limit: "1d"`:
- `_meta.client_channel` (C0B6JP9PX6C): where the client asks.
- `_meta.internal_channel` (C0B4L6NSCBY): where the team confirms moves.
Ignore bots and this skill's own posts. New client concern not in the ledger =
APPEND (`state:"open"`, source "client channel <date>"). A message that moves
an existing item updates its `status`+`last_update`. Never delete; flip to
`resolved`. Internal chatter only UPDATES existing items, never creates them.
Write the ledger back. If Slack errors, skip the scan (ledger alone still
feeds the line); retry at most once per channel. Select at most 2 items where
something MOVED yesterday (a shipped change, a client reply, a concrete
number/date), else an `open` item due within 2 days, else omit.

## Step 6 - Compose the state of affairs

Slack mrkdwn to `scripts/_cy_daily_update_report.txt` via Write. This is the
CEO-level read, in Edwin's order: lead with momentum, walk the improved funnel,
then the honest hard number with its n and the timing caveat, then what's next.
Fixed order so the team can eyeball deltas day to day.

```
cat years - cohort 2 state of affairs (freebie excluded), thru {yesterday}

momentum: {purchase-intent read vs c1 same-age - add-to-cart {X}x ({n_c2} vs {n_c1}), scroll-past-price {a}% to {b}%}. {one plain clause: are the good people moving through the improved funnel better than c1}
awareness/tof: {open on the READ, not the spend stat} hero held {hold}% this wk ({benchmark, e.g. vs the ~47% at launch}), so ~{plain outcome, e.g. half of everyone who starts it watches through} at {cpm/cheap-reach read vs target}. {mechanism if a number moved, e.g. hold slipped because the 30s cut trades depth for reach}. {IF a converting line ran: it carries the clicks at {ctr2}% while awareness holds {s}% of ${total} spend; move: shift ${x} off the hero into it | IF converting line dark: {converting lines} sat at $0, so re-fund the sample asc at ~${x} for the cohort-3 send, judged on sample-CPL vs $7 over ~5d}
creative: {winner concept} ({quoted hook line}) leads at {ctr}% ({vs the 8.29% sample avg}), hook {h}% / hold {hd}%; wins because {the one DNA beat: e.g. the proof claim lands in the first 3s for the pet-first health seeker who wants proof}. {loser concept} at {ctr2}% because {the beat that failed}. next test: {one controlled change} vs {named baseline}, read ~{window}
    {IF no sample static ran: no sample static ran this wk, the drinking-problem hero was all the meta spend, ad10/the ugc got $0. the 30s junior cut hooks {a}% vs the 60s master's {b}% but holds {c}% vs {d}%, so it trades depth for reach. next test: 30s vs 60s on thruplay at matched spend, read ~5d; re-brief the sample statics when the asc re-funds}
email: new flow (live {date}) {click2}% click ({n} sent) vs {click_old/click_c1}%, {over/under} the 1% healthy mark, aiming 2%. {open2}% open. needs ~1.5wk to confirm it holds
funnel: shopify add-to-cart / checkout / cvr trending {up/flat} (summer sale is a tailwind, noted)
buyers: {n} cohort-2 purchases so far ({premium}/{genpop}), vs {c1_n} for c1 at the same age. still early - c1's median delivered-to-buy was 6 days and only ~{pct}% of c2 is past that window, so expect this to climb
income cut (jordan's ask): c1 premium {p}% vs genpop {g}% ({X}x); c2 too early to split ({n} buyers)
whats next: {retargeting threshold status, {delivered}/13,000 in, rest {when}} · {dtc conversion launch timing} · {any client-qs item that moved, concrete fact only}
```

Lines with no data (e.g. income cut when c2 has 0 buyers and c1 unchanged) or
no movement (whats-next client item) collapse rather than pad. Never print a
line of filler.

### Voice (SOUNDING LIKE A BOT IS FAILURE)

Posts as Edwin. Read #cat-years if unsure. Lowercase, plain dashes, no bold, no
emoji, no mrkdwn labels, no bullet glyphs (plain "-"). Abbreviations: c1/c2, rt,
ga4, tt, gads, cvr, yest. Numbers like "4k", "$28", rates to 1 decimal,
thousands commas. He writes "broad is still winning on cheaper traffic and
engagement", not "*Audience:* broad outperforms".

- BREVITY IS THE RULE (Edwin 7/22: updates were too long, cut ~75%). Each line is
  the read plus the numbers that back it in ONE tight sentence, ~8-15 words. Keep
  every section and every number+n, strip all elaboration; the whole update should
  read in a glance. Detail that does not fit goes to a thread, never a longer line.
- NO VERDICT ABSTRACTIONS ("gates the funnel", "the blocker", "too early to
  call" as a label). Say what is literally happening and its consequence, the
  way a person types: "retargeting still off because the match list is under
  threshold, should cross mon/tue as more samples land".
- Lead with direction, the way Edwin does ("some momentum happening", "walking
  toward positivity"), but earn it with the number and n right next to it.
- NO "X, not Y" ANTITHESIS. "it's the business case, not the sample funnel" /
  "the discount pulling DTC, not cohort-2 maturing" are AI tells Edwin flags on
  sight. State the thing plainly and stop; if the contrast matters, make it a
  separate plain sentence. Same for punchy sentence-final fragments and tidy
  two-beat closers (statement + aphorism). Just say what happened.
- Run a DE-AIFY CADENCE PASS on the finished bullets before writing the file
  (separate from the em-dash scrub): reread each line for antithesis, punch
  closers, and label-jargon; rewrite any that read like copy instead of how a
  person types. See [[feedback_deaify_cadence_pass]].
- Don't restate context the team has (what the flows are, why freebies are out).
  Do not fake typos or force slang.

### Content rules

- Segment mix from `c2.segment_mix_exact`. Buyer count + split from the FRESH
  Shopify pull in Step 2.5 (not the stale facts number). If buyers n = 0 from a
  confirmed-fresh pull, say "0 so far" and lean on the timing caveat, do NOT
  read it as a failure. If the pull failed, use the flagged fallback.
- Timing caveat is standing doctrine (client brain learnings 5c/5d): cohort-1
  delivered-to-buy was median 6 days / mean 7.5 days, 87% within 14 days. A
  cohort is not judgeable until most of it is past ~1 week post-delivery. If
  `facts` gives per-day c2 deliveries, the "~{pct}% past the window" is
  deliveries that landed >=6 days before `facts.today` over total delivered;
  otherwise say "most of c2 is still inside the first week post-delivery".
- Income cut is Jordan's standing ask (learnings 5b): c1 premium ~0.85% vs
  genpop ~0.19% (~4.4x) is the mature read; recompute from facts if present.
  c2 stays "too early to split" until it has enough buyers (say the n).
- The read must answer: are the good people moving through the improved funnel
  better than c1 at the same age, and what happens next. Grounded only in the
  numbers above.
- awareness/tof + creative lines carry the SAME daily voice as everything else
  (lowercase, plain dashes, no labels/bold, ~8-15 words per line, de-aified). The creative
  line must quote the winning LINE and its DNA, not just name the ad, and end on
  one next test. The awareness line ends on a budget move (reallocate vs hold),
  never a bare metric recital. Both obey the Step 4.5 guardrails (statics carry
  the leads, hero gets variations only, no "scale ad10", no cross-funnel move
  without a live campaign). Judge the hero on hold + downstream harvest, never on
  its CTR.
- FIND NEW on the front of funnel too (playbook P6/P8): if the winner and the
  awareness read are the same as yesterday's post, collapse both to ONE plain
  "creative/awareness held (ad10 still leads at {ctr}%, hero spend flat)" line.
  Re-reading a winner that did not move is filler.
- If the creative-level pull failed, the creative line reads "creative-level read
  unavailable today (hq error)" and the awareness line degrades to the
  campaign-level ctr + spend-concentration read. Never fabricate a winner or carry
  yesterday's number forward.

Data-health: any failed pull or a stale-orders flag from `facts.data_health`
gets ONE honest clause on the relevant line ("orders export stale to 7/7,
undercounts"), never buried and never dressed up.

## Step 6.5 - Extend the playbook (only when you learned something durable)

If this run surfaced a genuinely NEW, generalizable analysis pattern (a reusable
way to read the data that would help future runs; skip one-day numbers), append
ONE line to the "Daily-update analyst playbook" in
`.claude/clients/cat-years/learnings.md` as the next P-number. Guardrails:
- Durable recipe only. Never write daily figures, buyer names, or one-off events.
- Dedupe: if it restates an existing P-recipe, do NOT add it.
- One line, plain cadence (the P7 de-aify rule applies to the playbook too).
- Most days add nothing. A dry run is the normal case; do not invent a pattern
  to have something to write.
The client brain is untracked, so this survives the SessionStart auto-update
reset. Never rewrite or reorder existing recipes; append only.

## Step 7 - Write and stop

Write to `scripts/_cy_daily_update_report.txt`. You are NOT responsible for the
Slack call. If the facts file is missing or `day_n` < 1, write an EMPTY file and
stop.

## What NOT to do

- Do not post to Slack, touch campaigns, or edit the dashboard/metrics JSON.
- Recompute cohort-2 BUYERS from the fresh Shopify pull (Step 2.5); the python
  facts buyer count reads a file that can be stale. Do NOT recompute the other
  cohort splits (recipients, freebie/premium/genpop mix, c1 same-age baseline),
  python did those exactly.
- Do not infer flow/delivery state from a failed pull (see Hard rules).
- Do not spawn subagents or use ToolSearch. Budget ~19 tool calls (2 Read,
  2-3 Klaviyo, 1-2 Shopify, 3-4 HQ incl. the Step 4.5 creative/campaign pulls,
  2 Slack, 2 Write). The Step 4.5 read is worth the extra HQ calls; keep it tight.
- Ledger is durable state: append/update, never wholesale rewrite or delete.
- Client-qs content reports only what WE did or the CLIENT said (facts with
  numbers/dates). Never speculate on client intent or promise uncommitted dates.
