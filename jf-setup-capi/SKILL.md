---
name: jf-setup-capi
description: "Set up Meta Conversions API (CAPI) for a Jetfuel client during onboarding. Generates platform-appropriate implementation (Shopify, Stripe, Node, Python) targeting EMQ 9.3 (the Aletha benchmark), wires browser+server dedup, and writes a SETUP.md for the client engineer. Use when the user says 'set up CAPI', 'CAPI onboarding', 'fix event match quality', 'low EMQ', 'configure pixel + server events', 'set up conversions API'."
disable-model-invocation: true
---

# /jf-setup-capi — CAPI Setup (Jetfuel)

Generate a production-ready Meta Conversions API implementation for a new (or struggling) JF client. Targets **Event Match Quality 9.3+** — the benchmark Aletha hit per `project_andromeda_audit_rubric.md` Pillar 2.2.

This skill produces a code package + setup instructions; it does **not** push code to the client's repo. The client engineer (or our integrations team) reviews and merges.

## Why CAPI matters in 2026

Per `project_andromeda_audit_rubric.md` Pillar 2 (Signal Hygiene, 3 of 14 points):
- CAPI + Advanced Matching ON
- Event Match Quality ≥7.0 (Aletha target: 9.3)
- Server-side first-party enhancement (Aimerce/Elevar/equivalent) OR 50+ optimization events/week

Andromeda needs signal to feed its model. Browser-pixel-only accounts get throttled. Without CAPI, you cannot win the 2026 auction.

## Arguments

- Client name. Default: ask.
- `--platform shopify|woocommerce|stripe|custom-node|custom-python` — Required.
- `--events "Purchase,InitiateCheckout,AddToCart,ViewContent,Lead"` — Comma-separated. Required.
- `--pixel-id` — Meta Pixel ID. Default: pull from HQ client config / Meta MCP.
- `--enhancement-vendor aimerce|elevar|none` — Server-side first-party tool, if any. Default: none.
- `--test-mode` — Use Meta's test event tool (TEST_EVENT_CODE) instead of production. Default: true.
- `--output-dir path` — Where to write the implementation. Default: `.claude/ops/jf-setup-capi/implementations/{client-slug}/`.

## Steps

### 1. Load identity, client context

- Read `.claude/me.md`. STOP if missing.
- Read `.claude/ops/jf-setup-capi/config.json` for vendor preferences, platform templates.
- `get_client(client_id)` → confirm client is real.
- `get_client_platforms(client_id)` → check existing Meta + ecommerce platform mappings, pull pixel_id if available.
- If pixel ID still unknown: `mcp__meta__meta_list_pixels(business_id={...})` and match by client domain.

### 2. Audit the current state first

Before generating anything, check what's already in place:
- Is the browser pixel installed? (WebFetch the client's site, look for `fbq('init', ...)`)
- Is CAPI sending any events? Use Meta MCP / Events Manager API to check the pixel's event sources.
- What's the current EMQ for Purchase? If above 9 already, the gap is elsewhere — surface that and ask if user wants to skip generation.

Output an "audit summary" before writing any code:
```
Current state for {client}:
- Browser pixel: ✅ installed at /, fbq init present
- CAPI: ❌ no server events in last 7 days
- EMQ Purchase: N/A (no events)
- Enhancement vendor: none configured

Gap: full CAPI implementation needed. Generating Shopify webhook handlers + Node CAPI module.
```

### 3. Generate the core CAPI handler

Output to `{output-dir}/capi-handler.js` (Node) or `.py` (Python). The handler exposes:

```js
sendCapiEvent({
  eventName,
  userData,    // hashed PII (email, phone, fn, ln, ge, db, ct, st, zp, country)
  customData,  // value, currency, content_ids, content_type
  eventId,     // for browser dedup
  eventSourceUrl,
  actionSource: 'website',
  testEventCode: process.env.META_TEST_EVENT_CODE || undefined
})
```

Use the official `facebook-nodejs-business-sdk` (Node) or `facebook-business` (Python). Set Advanced Matching fields per Meta's spec — every available customer field, hashed SHA-256 lowercase.

Include a `hashPii()` helper that lowercases + trims + SHA-256s — this is the single biggest EMQ lever.

### 4. Generate per-event handlers

For each `--events` entry, write `{output-dir}/events/{event}.js`:

**Purchase** — must include `event_id = order_id` for dedup with browser pixel. Map: `value=order.total`, `currency=order.currency`, `content_ids=order.line_items[].product_id`, `content_type='product'`. Include all customer PII fields.

**InitiateCheckout** — `event_id = checkout_token`, value + currency, content_ids.

**AddToCart** — `event_id = "atc-" + product_id + "-" + session_id`, value.

**ViewContent** — `event_id = "vc-" + product_id + "-" + session_id`, content_ids.

**Lead** — for lead-gen clients only.

Every event includes the `fbc` (from `_fbc` cookie) and `fbp` (from `_fbp` cookie) for click-attribution match.

### 5. Generate platform integration

**Shopify** — `{output-dir}/shopify-webhook.js`:
- Express POST route at `/webhooks/shopify/:event_type`
- HMAC verification against `Shopify-Hmac-Sha256` header using `SHOPIFY_WEBHOOK_SECRET`
- Mapping: `orders/paid → Purchase`, `checkouts/create → InitiateCheckout`
- Return 200 within 5 seconds (Shopify retries otherwise)

**Stripe** — `{output-dir}/stripe-webhook.js`:
- Stripe webhook signature verification
- `payment_intent.succeeded → Purchase`

**Custom Node/Python** — emit a generic handler the client wires into their existing checkout completion code path.

### 6. Generate the dedup config

`{output-dir}/dedup-config.md`:

```
## Browser pixel must fire with event_id matching CAPI

Browser side (add to thank-you page):
fbq('track', 'Purchase', {
  value: {{order.total_price}},
  currency: '{{order.currency}}',
  content_ids: [{{order.line_items[].product_id}}]
}, {
  eventID: '{{order.id}}'
});

CAPI side: setEventId(order.id)

Same event_id → Meta counts once. Different or missing event_id → double-count = bad EMQ + skewed conversions.
```

### 7. Generate the enhancement vendor wiring (if applicable)

If `--enhancement-vendor aimerce`: write `{output-dir}/aimerce-config.md` with the Aimerce CAPI passthrough config — per `project_andromeda_audit_rubric.md`, this is the JF Aletha implementation path.

If `elevar`: Elevar's GTM container template + the JF additions for advanced matching.

If `none`: include a recommendation to add one if EMQ stays below 9 after launch.

### 8. Generate the test script

`{output-dir}/test-events.js`:
- Sends one test event per `--events` entry
- Uses `test@example.com` (hashed), real `fbc`/`fbp` cookies if provided
- Hits Meta's Test Events endpoint (`test_event_code` in payload)
- Reports the EMQ response per event

### 9. Generate `.env.example`

```
META_CAPI_TOKEN=
META_PIXEL_ID=
META_TEST_EVENT_CODE=
SHOPIFY_WEBHOOK_SECRET=
AIMERCE_API_KEY=   # if applicable
```

### 10. Generate the client-facing SETUP.md

`{output-dir}/SETUP.md` written for the client engineer:

```
# Meta CAPI Setup — {client}

## What this gives you
- EMQ target: 9.0+ (current baseline: {n})
- 5 events tracked server-side: Purchase, InitiateCheckout, AddToCart, ViewContent, Lead
- Browser+server deduplication via event_id = order_id

## Install
1. npm install facebook-nodejs-business-sdk express
2. Copy `capi-handler.js`, `events/*.js`, `shopify-webhook.js` into your backend
3. Add env vars (see .env.example)
4. Configure Shopify webhook: orders/paid → POST {your-domain}/webhooks/shopify/orders-paid
5. Add the eventID block to your thank-you page (see dedup-config.md)
6. Verify in Events Manager test events tab (use test code from env)
7. Remove test code from env, deploy

## Verify EMQ
After 24h of live traffic, check Events Manager → Data Sources → Pixel → Diagnostics.
Target: EMQ 9.0+ on Purchase. Below 7 → triage hashing + missing fields.

## Tickets we'd file if EMQ stays low
- Missing first/last name on customer object → contact Shopify/auth pipeline
- IP/UA not captured server-side → check Express middleware
- Click ID (fbclid) not stored → check session storage
```

### 11. Write the JF audit entry

After generation, optionally call HQ `client_changes` to log "CAPI implementation generated for {client}, EMQ target 9.0, vendor={x}" so the next engagement check sees this artifact.

### 12. Present in-conversation summary

```
CAPI implementation generated for {client} at {output-dir}.
- Platform: {platform}
- Events: {events}
- Test mode: {on/off}
- Enhancement vendor: {vendor}

Next: hand SETUP.md to {client_engineer_email_from_brief} for review + merge.
Target EMQ post-launch: 9.0+. If we land below 7, schedule a triage call.
```

## Important Rules

- **Never commit code to a client repo.** This skill generates files locally; humans review and merge.
- **EMQ 9.3 is the Aletha-tier target.** ≥7.0 is the audit floor; 9.0 is good; 9.3+ is the playbook ceiling per `project_andromeda_audit_rubric.md`.
- **Browser pixel must remain.** CAPI is *in addition to* the browser pixel, not a replacement. Both fire, dedup catches duplicates. Removing the browser pixel destroys click-through attribution.
- **Hash everything.** Email, phone, names — SHA-256 lowercase trimmed. The number one EMQ killer is missing or unhashed PII.
- **Test mode default ON.** Move to production only after the test events tab shows green for 24h.
- **No HTTP token scripts.** Use the official Meta SDK (`facebook-nodejs-business-sdk` / `facebook-business`). Per `feedback_no_mcp_http_scripts.md`, no DIY bearer-token loops.
- **Surface enhancement-vendor option.** Aimerce/Elevar/equivalent gets you the last mile to 9.3 — recommend if EMQ projection is below 9.
- **Display all times in user's timezone.**

## Config

`.claude/ops/jf-setup-capi/config.json`:

```json
{
  "defaults": {
    "events": ["Purchase", "InitiateCheckout", "AddToCart", "ViewContent"],
    "test_mode_default": true,
    "emq_target": 9.0,
    "emq_floor": 7.0,
    "emq_aletha_benchmark": 9.3
  },
  "templates": {
    "shopify": "templates/shopify/",
    "woocommerce": "templates/woocommerce/",
    "stripe": "templates/stripe/"
  },
  "preferred_enhancement_vendor": "aimerce"
}
```

## Why this skill exists

External `/setup-capi` generates a generic implementation. The JF version targets EMQ 9.0+ specifically (because that's what Andromeda needs), includes the enhancement-vendor recommendation (because Aletha's 9.3 came from Aimerce), and audits the current state BEFORE generating code so we don't ship 800 lines of Node for an account that already had CAPI fine and just needed an EMQ tune.
