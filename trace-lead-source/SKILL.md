---
name: trace-lead-source
description: Use when a new inbound lead comes in (HubSpot form submission, contact created) and you need the real acquisition source, especially when the CRM shows "direct", "organic", or no referrer. Triangulates HubSpot + GA4 + Gmail/Slack to catch AI-assistant and dark-traffic leads the CRM mislabels.
disable-model-invocation: true
---

# Trace Lead Source

Find where an inbound lead actually came from by triangulating three systems. The CRM alone is not trustworthy for source. HubSpot buckets AI-assistant referrals (ChatGPT, Claude, Gemini, Perplexity) and other referrer-stripped traffic as `DIRECT_TRAFFIC`. GA4 is the only system that preserves the true channel. This skill exists to stop you reporting "direct" when the lead was really an AI-sourced or dark-funnel lead.

## The core rule

**Never report the lead's source from HubSpot's source field alone. Always cross-check GA4 by conversion timestamp.**

If HubSpot says `DIRECT_TRAFFIC` / `ORGANIC` / null referrer, dig in GA4 before you conclude anything. Match the lead to its GA4 session by the minute it converted, and let GA4's channel win.

## Inputs

From the webhook payload (or manual invocation):
- **Lead email** (required), e.g. `mallory@saintspritz.com`
- HubSpot **contact id** if provided (skips the lookup search)

Derive the **company domain** from the email (`saintspritz.com`).

## Steps

### 1. Pull the HubSpot record
Use `hubspot-search-objects` (objectType `contacts`) by email, or `hubspot-batch-read-objects` if you have the id. Request these properties:
`email, firstname, lastname, company, phone, createdate, hs_analytics_source, hs_latest_source, hs_analytics_source_data_1, hs_analytics_source_data_2, hs_latest_source_data_1, hs_analytics_first_url, hs_analytics_first_referrer, first_conversion_event_name, recent_conversion_event_name, lifecyclestage`.

Capture:
- **Conversion timestamp** = `createdate` (this is UTC, ISO-8601).
- The form's own fields (budget, message). These usually are not stored as contact properties. Get them from the **HubSpot Forms notification email**: search Gmail for sender `noreply@notifications.hubspot.com`, subject starting `You've got a new submission on the HubSpot Form`, matching the lead. If that email is not found, leave the fields blank. Do NOT fabricate them.
- HubSpot's claimed source (`hs_analytics_source` + `hs_analytics_source_data_1`).

### 2. Convert the timestamp to Pacific
The GA4 property timezone is **America/Los_Angeles**. HubSpot `createdate` is UTC.
Convert and record the **PT hour bucket** (0-23). Do it with `zoneinfo` so DST is automatic (do not hand-subtract hours):

```python
from datetime import datetime
from zoneinfo import ZoneInfo
utc = datetime.fromisoformat("2026-07-24T15:40:26+00:00")   # HubSpot createdate, force +00:00
pt  = utc.astimezone(ZoneInfo("America/Los_Angeles"))
print(pt.isoformat(), "hour =", pt.hour)                     # 2026-07-24T08:40:26-07:00 hour = 8
```

### 3. Cross-check GA4 (the decisive step)
jetfuel.agency property = `256406873`. The runner is stdlib-only. Run BOTH queries for the lead's conversion date (`{DATE}` = YYYY-MM-DD, PT):

The output is large (tens of KB), so **redirect each to a file and parse the file**. Do not try to eyeball raw stdout.

```bash
# A. The conversion event, by source + hour + geo
python scripts/ga4_query.py --property 256406873 --start {DATE} --end {DATE} \
  --dimensions eventName,sessionSourceMedium,hour,region,city --metrics eventCount --limit 5000 --json > a.json

# B. The landing page + channel the session entered on
python scripts/ga4_query.py --property 256406873 --start {DATE} --end {DATE} \
  --dimensions sessionDefaultChannelGroup,sessionSourceMedium,landingPagePlusQueryString,region,city \
  --metrics sessions,keyEvents --limit 5000 --json > b.json
```

`ga4_query.py` has **no server-side filter** and defaults to a low limit, so always pass `--limit 5000` and filter the JSON in a short python block that reads the file. Look for:
- **Conversion events** in `a.json`: event names containing `lead`, `form`, `submit`, `generate`. This property fires BOTH `form_submit` and `lead_with_source` for one submission. Treat them as a single conversion, do not double-count.
- The row(s) whose **hour matches** the lead's PT hour from step 2.
- In `b.json`, the row(s) with `keyEvents > 0`, which give the landing page.
- Delete `a.json` / `b.json` when done.

### 4. Match and reconcile
Match the lead to a GA4 session using, in priority order:
1. **Hour**: the conversion event fired in the same PT hour bucket.
2. **Uniqueness**: often it is the only key-event of the day, which makes the match near-certain.
3. **Geo**: GA4 region/city is consistent across the session's events. A phone area code is NOT geo. Do not use it. Use GA4's region/city.
4. **Content fit**: the landing page topic matches the lead's company/industry (a CPG brand landing on a CPG-strategy post is a strong tie).

Note the two queries carry different dimensions: `a.json` (the event) has `hour` but no landing page; `b.json` (the landing page) has no `hour`. So anchor the event in `a.json` by hour, then bridge to the landing page in `b.json` by **shared source + geo**, not by hour.

**AI Assistant channels** show up as `claude.ai / ai-assistant`, `chatgpt.com / ai-assistant`, `gemini.google.com / ai-assistant`, `perplexity.ai / ai-assistant`. When HubSpot says `DIRECT_TRAFFIC` but a matching GA4 session shows one of these, **GA4 is correct** and HubSpot dropped the referrer.

If the landing page is a blog/content URL and the source is an AI assistant, label it a **Dark SEO Funnel / AIO lead**: an LLM ingested our content and recommended us, invisible to GSC organic. GSC only captures Google organic search, so its silence here is confirming rather than contradictory.

### 5. Human context (fast, optional)
- `search_gmail_messages` for the domain to find the reply thread (who responded, meeting booked, other contacts CC'd).
- Slack search for the company/lead name in case sales already touched it.

### 6. Assign confidence
- **High**: GA4 event matches on hour AND (unique key-event OR consistent geo).
- **Medium**: plausible GA4 session same day but hour/geo ambiguous (multiple candidates).
- **Unconfirmed**: no matching GA4 event. Say so plainly. Report HubSpot's field as the only signal and note it is unreliable for AI/dark traffic. **Never invent a source.**

## Output

Write a compact verdict, then deliver to BOTH destinations.

**Verdict block:**
```
Lead: {name} ({email}) | {company}
Converted: {DATE} {HH:MM} PT via "{form/conversion event name}"
Source (GA4): {sessionSourceMedium}  [{channel group}]
Landing page: {landingPagePlusQueryString}
Geo (GA4): {city}, {region}
HubSpot said: {hs_analytics_source} / {source_data_1}   [MATCHES or WRONG, referrer stripped]
Confidence: {High/Medium/Unconfirmed}
Read: {one line, e.g. "AI-sourced (Claude) Dark SEO Funnel lead off the CPG retail post"}
```

**Deliver to both:**
1. **Slack**: post the verdict to the configured leads channel via the Slack MCP send-message tool. (Edwin's instance uses `#ai_edwin_claude`, C0APU39TP50. Chris sets his own channel in the webhook config.)
2. **HubSpot note**: attach the verdict to the contact with `hubspot-create-engagement` (type `NOTE`), associated to the contact id, so the real source lives on the record next to HubSpot's field.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Reporting HubSpot's "direct traffic" as the answer | Direct/organic/null means dig in GA4 by timestamp. GA4 wins. |
| Using the phone area code as location | Area code is not location. Use GA4 region/city only. |
| Low `--limit` on ga4_query.py | Always `--limit 5000`. The tool truncates silently and the lead's row vanishes. |
| Matching on UTC hour | GA4 `hour` is PT. Convert HubSpot UTC to PT first, mind DST. |
| Guessing a source when GA4 has no match | Mark Unconfirmed. Never fabricate attribution. |
| Reading GSC silence as "no source" | GSC only sees Google organic. AI-assistant leads are invisible there by design. |

## Notes for maintainers
- GA4 access runs on the marketing@ ADC (`ga4-user-adc.json`) behind `scripts/ga4_query.py`. Do not POST to any MCP/GA4 endpoint with a copied bearer token. Use the script and the native HubSpot/Slack MCP tools.
- Event names are property-specific. If `form_submit`/`lead_with_source` stop matching, re-list event names with query A and update this file.
- Webhook wiring (HubSpot form-submission to per-lead run to both outputs) is in `WEBHOOK.md`.
