# Offer-Market Fit — Methodology

The encoded CTC method behind the `offer-market-fit` skill. Read this before running.

Source spine: CTC, [Offer-Market Fit: Why 7-Figure Brands Hit a Wall](https://commonthreadco.com/blogs/ecommerce-playbook/offer-market-fit-why-7-figure-brands-hit-a-wall)
(Joy Sharma, PE7 program). Unit-economics layer from CTC's
[daily contribution margin](https://commonthreadco.com/blogs/coachs-corner/track-contribution-margin-daily)
and [unlocking profit](https://commonthreadco.com/blogs/ecommerce-playbook/unlocking-profit-hardest-most-important-part-scaling)
writing.

---

## The thesis

Offer-market fit = your proposition aligns with what an audience segment will buy, at a
price point that lets you **compete profitably in the ad auction**. Growth plateaus are
business problems wearing a marketing costume. At $500/day you beat unsophisticated
competitors; as you spend more you compete against brands with better margins, better
merchandising, and higher conversion rates who can afford a CAC above your AOV. When that
happens, creative volume has only a ~10-20% improvement ceiling. The fix is the offer, not
the ad.

**The sequence is non-negotiable:**

```
product-market fit  →  offer-market fit  →  creative strategy
(demand exists)        (unit economics win)   (volume + variation pays off)
```

Reversing it is "where businesses go to die." Creative is a *volume* mechanism, not an
*efficiency* tool, once offer-market fit exists.

---

## Phase 0 — Unit-economics truth (the scoreboard)

Pull and reconcile these. State the source of each number.

| Metric | Definition | Primary source | Fallback |
|---|---|---|---|
| AOV | Average order value | Shopify net sales ÷ orders | Meta `conversion_value ÷ purchases` |
| CVR | Site conversion rate | Shopify orders ÷ sessions (ShopifyQL) | GA4 sessions→conversions; tag source |
| Spend | Ad spend in window | HQ `client_performance` / `get_platform_insights` | — |
| New-customer CAC | Spend ÷ *new* customers | HQ Meta (new-customer purchases) | Spend ÷ all purchases; label "blended" |
| CPM | Cost per 1,000 impressions | HQ Meta | — |
| CTR | Click-through rate | HQ Meta | — |
| CPC | Cost per click | HQ Meta | Derive: **CPC = CPM ÷ CTR** (sanity check) |
| COGS, shipping, fulfillment, payment fees | Variable costs/order | config / client-supplied | `[NEEDS REAL DATA]` |

**Contribution margin per order** (CTC's scoreboard — "are you winning or losing by the one
thing that matters, money in your pocket"):

```
CM/order = AOV − COGS − shipping − fulfillment − payment fees − CAC
```

If any cost input is missing and not in config, prompt once. If still missing, report
CM/order as `[NEEDS REAL DATA]` and proceed with the auction-position tests (which only need
AOV and CAC).

---

## Phase 1 — Diagnosis (OFFER vs CREATIVE vs PRODUCT)

Run all three tests, then issue one verdict.

### Test 1 — AOV-to-CAC (the structural ceiling)

```
if industry_CAC ≥ AOV:  → structural ceiling. You cannot win at scale on this offer.
```

CTC example: a jewelry brand with **$100 AOV** facing an industry CAC of **$110** cannot
compete, no matter the creative. The room to operate is `AOV − industry_CAC`; the wider it
is, the more auction headroom you have.

### Test 2 — AOV↔CVR log curve (the perceived-value signal)

Lower-AOV products must convert at a higher rate to be viable; higher-AOV products tolerate
low CVR. Plot the brand's `(AOV, CVR)` against the curve. **Below the curve = perceived
value too low for the price** → an offer problem. CTC anchors: a **~$40** product needs
**~6%** CVR; a **~$1,000** product needs only **~1-2%**.

**Heuristic curve `[ESTIMATE]`** — use ONLY when no real benchmark is available, and label
it an estimate in the output. Log-interpolated from the two CTC anchors above:

| AOV band | Required CVR to be "on curve" `[ESTIMATE]` |
|---|---|
| ~$25 | ~7.5% |
| ~$40 | ~6.0% |
| ~$60 | ~5.0% |
| ~$100 | ~4.0% |
| ~$150 | ~3.2% |
| ~$250 | ~2.6% |
| ~$500 | ~2.0% |
| ~$1,000 | ~1.5% |

Read it as: brand CVR **≥** the band value → on/above curve (good); below → perceived-value
gap. This table is a directional heuristic, not measured market data. A real
vertical-specific curve (client/Northbeam data) always overrides it.

### Test 3 — Creative gate (rule creative in or out)

Creative is adequate when:

```
CTR > 2%   AND   CPC ≈ $1 (CPM ÷ CTR)
```

If creative metrics are already healthy but the account won't scale profitably, the wall is
**not** creative — it's the offer. Creative quality only buys ~10-20% once the offer lacks
fit. (After offer-market fit, the creative "hit rate" benchmark rises from ~2% to ~7%.)

### Verdict logic

```
industry_CAC ≥ AOV ......................... OFFER problem (structural). Engineer the offer.
(AOV, CVR) below curve & creative healthy .. OFFER problem (perceived value). Engineer it.
creative metrics weak (CTR<2%, CPC high) ... CREATIVE problem. Hand to creative skills.
demand/retention absent, repeat rate poor .. PRODUCT problem. Say so; don't paper over it.
```

State the verdict in one line with the numbers behind it. Only an OFFER verdict proceeds to
Phase 2.

---

## Phase 2 — Engineer offers (perceived value)

Goal: lift target AOV and/or perceived value so the offer clears the curve and funds a CAC
that wins the auction. CTC levers:

- **Bundle** the hero product with high-margin items (raises AOV and margin together).
- **Set-based pricing** — "only buy in sets of two" — forces AOV up.
- **Incentives** — free gift, package-only pricing, threshold discount.
- **Advertorial-style landing page** — sells the value before the price.
- **Friction removal** — fewer checkout steps; faster path to purchase.

Output **3-5 candidate offers**. Each row:

| Offer | Lever(s) | Target AOV | Required CVR @ that AOV | Est. CM/order | Notes |
|---|---|---|---|---|---|
| Hero + free gift, set of 2 | bundle + set pricing + gift | $X | (from curve) | $Y `[NEEDS REAL DATA]` if cost inputs missing | … |

The "Required CVR" comes from the curve at the new target AOV. The offer wins if you believe
the bundle's perceived value can hit that CVR while the margin still funds the target CAC.

---

## Phase 3 — Marketing-moment test plan

CTC tests offers as **time-bound "marketing moments,"** not evergreen, to eliminate
downside risk.

Design rules:
- **Cultural-moment timing** — anchor to Father's Day, Back to School, a seasonal event, a
  drop. (Use `--moment` if supplied.)
- **Unlisted** — keep the offer off the main catalog/nav to protect organic traffic.
- **Incremental** — the test must add revenue, not cannibalize existing sales.
- **Statics only** — isolate the offer from production value; cheap to run; if a static
  offer wins, video will only amplify it.

Success thresholds:

| Signal | Target |
|---|---|
| Creative hit rate | 2% pre-OMF, rising toward **7%** once the offer fits |
| Position on curve | `(AOV × CVR)` sits **above** the industry curve |
| CAC | affordable — at or only slightly above industry CAC |

**Graduation to evergreen** (when a moment offer wins):
1. Move the offer from limited-time → permanent funnel.
2. Expand creative variations (add video + more statics).
3. Scale spend until the CAC ceiling is reached.
4. Repeat the cycle with the next offer.

---

## Benchmark resolution (priority order)

The industry CAC and the AOV↔CVR curve are the two inputs we cannot pull from CTC's
proprietary dataset. Resolve in this order and **state which was used**:

1. **User/client-supplied** (`--benchmark`, Northbeam export, client data) → used as real.
2. **Meta `ads_insights_industry_benchmark`** (vertical CPM/CTR/CVR) → derive an estimated
   industry CAC. Tag `[ESTIMATE]`.
3. **Heuristic curve above** → last resort. Tag `[ESTIMATE]`.

Hard rule: anything not from real data is tagged `[ESTIMATE]` and never stated as a client
fact (`feedback_no_fabricated_data`).

---

## Data-source notes

- **HQ Meta tools** need `load_clients_tools` for `list_clients` / client resolution; the
  reporting reads (`client_performance`, `get_platform_insights`, `campaigns_performance`,
  `top_creatives`) are always visible.
- **Shopify MCP** connects to one store at a time. Confirm the connected store matches the
  client (`get-shop-info`); `switch-shop` if not. If the client's store isn't connected,
  fall back to Meta-derived AOV and flag the CVR source.
- **New-customer CAC** is the right denominator (CTC). If HQ only exposes blended purchases,
  label the CAC "blended" so the reader knows it understates true acquisition cost.

---

## Worked sanity-check (illustrative math, not a client)

A brand at **$45 AOV**, **3.5% CVR**, industry CAC `[ESTIMATE]` **$38**:
- Test 1: $38 < $45 → not a hard structural ceiling, but thin ($7 of auction headroom).
- Test 2: curve says ~$45 AOV needs ~5.5% CVR; brand is at 3.5% → **below curve**,
  perceived-value gap.
- Test 3: if CTR is 2.4% and CPC ~$0.90 → creative is fine.
- **Verdict: OFFER problem (perceived value).** Engineer a bundle that lifts AOV to ~$70+
  (curve target ~4.6%) so the margin can fund a CAC that wins the auction.

These numbers are illustrative to show the logic. Never present them as any client's data.
