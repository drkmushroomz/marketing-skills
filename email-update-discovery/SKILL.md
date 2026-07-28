---
name: email-update-discovery
description: Dev harness for the auto-discovery step in the daily email digest (scripts/email_update.py). Use to test, tune, or extend how the 8am digest finds unlabeled inbox threads that need Edwin's attention. Triggers: "email discovery", "digest is missing items", "tune the email auto-detect", "why didn't X show in the digest".
---

# Email Update Discovery

Local dev skill for the auto-discovery layer added to the daily digest on 2026-07-20.
This is a working notebook for iterating on the classifier.

## What it does

`scripts/email_update.py` (the 8am `\Jetfuel\EmailUpdate` cron) used to be a pure
renderer of hand-applied Gmail labels (`00 Email Updates/Needs Response` +
`Needs Follow Up`), so anything Edwin had not tagged never appeared. Discovery adds
a heuristic pass (pure Python, no LLM) that scans the inbox once and surfaces two
kinds of unlabeled threads.

Digest now = manual-labeled threads + Needs Action + auto-detected needs-response
+ auto-detected awaiting-reply + HubSpot rotation.

## Where the code lives

All in `scripts/email_update.py`:
- `discover_threads(svc, exclude_ids, today_pt)`: one inbox scan, returns
  `(needs_response, nr_trunc, awaiting_reply, ar_trunc)`.
- `build_exclusion_query()`: assembles the `-exclusion` query from config.json + me.json.
- Filters: `is_bulk_or_automated(t)`, `is_low_signal(t)`, `edwin_addressed(t)`,
  `edwin_participant(t)`, `has_human_external(t)`, `thread_senders(t)`, `last_headers(t)`.
- `_dedupe_cap(threads)`: collapse same sender+subject to newest, cap, report overflow.
- Constants near the top: `DISCOVERY_LOOKBACK_DAYS`, `DISCOVERY_MAX_FETCH`,
  `DISCOVERY_MAX_SHOW`, `AWAIT_FLOOR_DAYS` (env-overridable via
  `EMAIL_UPDATE_AWAIT_FLOOR`), `AUTOMATED_SENDER_RE`, `CALENDAR_SUBJECT_RE`,
  `FINANCIAL_SUBJECT_RE`, `FINANCIAL_SENDER_RE`.
- `render_html(...)` renders the "Needs Response: Auto-detected (not yet labeled)"
  and "Needs Follow Up: Auto-detected (you sent last, no reply)" sections, plus
  the previously-dead "Needs Action" label section.

## The two buckets (a thread is surfaced when ALL hold)

Common to both: in inbox, activity within `DISCOVERY_LOOKBACK_DAYS` (30); not
muted; not bulk/automated (`List-Unsubscribe`/`List-Id`/`Precedence`/`Auto-Submitted`
/`AUTOMATED_SENDER_RE`); not low-signal (calendar invite or financial, since me.json
`financial_emails` = "skip"); not already carrying a `00 Email Updates/*` label;
deduped by sender+subject; capped at `DISCOVERY_MAX_SHOW` (25) with overflow reported.

**needs_response** (ball in Edwin's court):
- Latest message sender is EXTERNAL (not `@jetfuel.agency`).
- Edwin is a direct To/Cc recipient of that latest message.

**awaiting_reply** (ball on them, Edwin should nudge):
- Latest message sender is INTERNAL (Edwin or a teammate like Febe).
- Edwin participated in the thread (`edwin_participant`).
- A real external human has posted in the thread (`has_human_external`).
- The thread has been silent for at least `AWAIT_FLOOR_DAYS` (2) since that last
  JF message, so Edwin is not nagged the same day he sent.

## Worked example (the case that prompted this)

Thorsten Ulbrich (`hrubash@gmx.de`, HubSpot lead, spa in Spain per Edwin's context)
in thread "Marketing Help" (`19f4cdba95e6de3a`). He went quiet after Febe tried to
schedule; JF sent last. The old digest never surfaced it because it was unlabeled
and JF-sent-last. It now lands in awaiting_reply once silence reaches 2 days.
Verified: with `EMAIL_UPDATE_AWAIT_FLOOR=0` the thread surfaces immediately.
Note the email never says "spa"/"Spain"/"meta audit"; the subject is "Marketing Help".

## How to test (never sends)

```
python scripts/email_update.py --dry-run
# force the outbound-waiting floor to see everything JF-sent-last:
EMAIL_UPDATE_AWAIT_FLOOR=0 python scripts/email_update.py --dry-run
```

Writes `scripts/_email_update_preview.html` and prints a summary: labeled counts,
both auto-detected lists (`sender | subject`), and truncation counts. Open the
preview HTML to see the rendered digest. Auth uses the Workspace MCP token; run
`/connect` first if it 401s.

## Tuning knobs

- Too much noise: tighten `AUTOMATED_SENDER_RE` / `FINANCIAL_*`, drop
  `DISCOVERY_LOOKBACK_DAYS`, raise `AWAIT_FLOOR_DAYS`, or add `-category:` filters.
- Missing real items: widen `DISCOVERY_LOOKBACK_DAYS`, lower `AWAIT_FLOOR_DAYS`,
  or loosen a filter.
- Exclusions come from config.json (`gmail_search_query`) and me.json
  (`gmail.search_exclusions`, `skills.email-update.preferences.skip_domains`), the
  same sources the `/email-update` skill uses. Mute a thread via the script's
  `MUTED_THREADS` (keep in sync with me.md).

## Known gaps / next dev ideas

- Classifier is external-facing only; internal 1:1s that need Edwin's reply are
  not caught (kept manual to hold noise down).
- No priority weighting yet (me.json `priority_topics` = business development, new business).
- Could learn from labels: when Edwin labels or archives a discovered item, feed
  that back so the same thread is not re-surfaced.
- HubSpot leads object is scope-blocked for the MCP token (`crm.objects.leads.read`),
  so lead status cannot cross-reference the digest yet.

## Rules

- No em dashes anywhere in output (Edwin hard rule). Brand is "jetfuel.agency".
- Never send from this script except the real (non-dry-run) digest to edwin@jetfuel.agency.
- Durability: the crew SessionStart auto-update hard-resets tracked files to
  origin/master and wipes unpushed work. The behavior lives in the tracked file
  `scripts/email_update.py`, so it must be committed and pushed to master to survive
  the next 8am run. This skill doc is untracked and survives resets. See the
  crew-autoupdate note in auto-memory.
