# trace-lead-source: webhook wiring (Chris)

How to run `trace-lead-source` automatically on every inbound lead. Read `SKILL.md` first for the method itself. This file is only the plumbing.

## Flow

```
HubSpot form submission
      -> HubSpot workflow (webhook action)
            -> Chris's endpoint (small listener)
                  -> invoke Claude headless with the skill + lead email/contact id
                        -> posts verdict to Slack + writes HubSpot note
```

## 1. HubSpot trigger

Create a HubSpot **workflow** (contact-based), enrolment trigger = "Form submission" on the contact forms you care about (e.g. "Contact Form 2026"). Add a **Webhook** action:
- Method: `POST`
- Target: Chris's listener URL
- Body includes at minimum: contact `email`, `hs_object_id`, and the form `createdate` / submission time.

A contact-created trigger works too, but form-submission is cleaner because it carries the conversion moment.

## 2. Listener

A minimal service (whatever Chris already runs for the Slackbot is fine) that receives the POST and launches the skill headlessly, passing the lead email and contact id. Pattern:

```bash
claude -p "Use the trace-lead-source skill for lead email={{email}} contact_id={{hs_object_id}}" \
  --dangerously-skip-permissions
```

Run it from the crew repo root so `scripts/ga4_query.py` resolves. Keep the prompt in a file and feed it via stdin if the shell mangles quoting (see the Cat Years insights-cron learning: never inline a headless prompt with `<...>` in a `.bat`).

## 3. Timing: mind the GA4 lag (important)

GA4's Data API does not surface a session the instant it happens. The AI-Assistant channel row for a brand-new lead can take a few hours, up to ~24h, to appear. If the webhook fires the skill immediately, the GA4 cross-check may come back empty and the lead gets marked **Unconfirmed** even though it was really AI-sourced.

Two ways to handle it, pick one:
- **Delay (recommended):** queue the lead and run the skill on a lag (e.g. next morning, or +6h). Simple, and GA4 has settled by then. A once-daily batch over the prior day's leads is the most reliable and cheapest.
- **Run-now + reconcile:** fire immediately for the HubSpot/Gmail context, and if GA4 has no match, requeue one retry after the lag before finalising.

For "every time a lead comes in," the delayed run still gives same-day attribution and avoids false Unconfirmeds. Do not treat an immediate empty GA4 result as "direct."

## 4. Config Chris sets

- **Slack channel** for the verdict (his own leads channel; Edwin's instance uses `#ai_edwin_claude`).
- **GA4 property**: `256406873` for jetfuel.agency, already in the skill. Confirm his `scripts/ga4_query.py` + marketing@ ADC resolve on his machine (he has GA4 access).
- **HubSpot**: the skill writes the note via the HubSpot MCP `hubspot-create-engagement`. No extra token handling.

## 5. Guardrails

- Idempotency: key on contact id so a resubmit does not double-post. Skip if a trace note already exists on the contact.
- Never POST to an MCP endpoint with a copied bearer token. The skill uses the GA4 script and native HubSpot/Slack MCP tools only.
- Cost: one lead = one short headless run. The daily-batch option bounds it further.
