---
name: heartbeat
description: Daily cron health monitor — reads pre-collected facts, writes a Slack report file for the wrapper to post
---

# Heartbeat — Cron Job Health Monitor

All scheduled jobs run locally via Windows Task Scheduler. The wrapper `scripts/heartbeat_claude.ps1` runs `heartbeat.py --facts-only` first, so **facts are already collected** at `scripts/_heartbeat_facts.json`.

Your job is narrow: **read facts → Write the final Slack report to `scripts/_heartbeat_report.txt` → stop.** The wrapper posts it.

Do not re-query `schtasks`, re-check auth, crawl Slack history, or post to Slack directly — Python already did it / will do it.

## Step 1 — Read the facts

`Read scripts/_heartbeat_facts.json`. The JSON is the source of truth:

```json
{
  "today": "YYYY-MM-DD",
  "yesterday": "YYYY-MM-DD",
  "crew_version": "abc1234",
  "auth": {"google_oauth_gsc": {...}, "google_sheets": {...}, "statamic_mcp": {...}, "slack": {...}, "ahrefs_mcp": {...}},
  "tasks": [{"name": "\\Jetfuel\\X", "state": "Enabled"|"Disabled", "last_result": "0"|other, "last_run": "...", "next_run": "...", "task_to_run": "..."}, ...],
  "slack_evidence": {"daily_blog_upgrade": {"when": "...", "preview": "..."}|null, "heartbeat": {...}|null, "ngram": {...}|null},
  "offboarded_hints": [{"file": "project_X.md", "title": "...", "snippet": "..."}]
}
```

## Step 2 — Classify each task

For each `tasks[*]`:

| Condition | Status |
|---|---|
| `state=Enabled` AND `last_result` in `0` / `267009` AND expected evidence present (see table below) | `OK` |
| `state=Enabled` AND `last_result` in `0` / `267009` AND expected evidence MISSING | `WARN — ran but no Slack/Sheet post` |
| `state=Enabled` AND `last_result` not in `0` / `267009` / `267011` | `FAIL — exit code {code}` |
| `state=Enabled` AND `last_result="267011"` (never run) AND `next_run` in future | `PENDING` |
| `state=Disabled` AND name matches an `offboarded_hints` entry | `OFFBOARDED` (expected, not an issue) |
| `state=Disabled` AND no offboarding match | `DISABLED — why?` (flag it) |

`267009` = `SCHED_S_TASK_RUNNING` — schtasks reports this when a task is querying itself mid-run (which the heartbeat task always does). Treat as success.

Expected evidence map (only a few jobs have externally observable signals):

| Task name pattern | Evidence key in `slack_evidence` | Expect within |
|---|---|---|
| `DailyBlogUpgrade` | `daily_blog_upgrade` | yesterday or today |
| `Heartbeat` | `heartbeat` | yesterday or today |
| contains `Ngram` or `N-Gram` | `ngram` | last 14 days (biweekly) |

For tasks without evidence keys, rely on `last_result` alone.

## Step 3 — Root-cause diagnosis (only on failures)

If any task is `FAIL`, add a one-line hypothesis based on the exit code:

- `1` → generic script failure; point at `task_to_run` path
- `-2147024894` / `0x80070002` → file not found; interpreter path probably bare — recommend `schtasks /Change /TN "..." /TR "<absolute-path>"`
- `267011` → never run (often fine for new or future-scheduled tasks)
- Slack/Sheets/Statamic-MCP/OAuth `ok:false` → include the short error string from the auth block

Do NOT apply fixes automatically in this run — just report. (The prior self-fix behavior was a liability; we'd rather surface and have a human approve.)

## Step 4 — Build the Slack message

Use Slack `mrkdwn`. Keep it scannable. Template:

```
*:heartbeat: Heartbeat Report — {today}*

*Auth:* {one line of emoji per service, e.g. :white_check_mark: OAuth | :white_check_mark: Sheets | :white_check_mark: Statamic | :white_check_mark: Slack | :white_check_mark: Ahrefs}

*Tasks:*
:white_check_mark: `\Jetfuel\DailyBlogUpgrade` — last run {last_run}, evidence OK
:warning: `\Jetfuel Biweekly N-Gram + Ad Copy` — last run {last_run}, no recent Slack evidence
:no_entry: `\Ngram-Barker-Weekly` — disabled (offboarded 2026-04-10)
...

{only if failures:}
*:rotating_light: Action Needed:*
• `\Jetfuel\X` failed with exit {code} — likely {hypothesis}. Check `{task_to_run}`.

crew version: {crew_version}
```

Keep it under ~25 lines. Omit sections that have nothing in them.

## Step 5 — Write the report file

Use the Write tool to save the Slack mrkdwn body from Step 4 to `scripts/_heartbeat_report.txt`. The PowerShell wrapper reads that file and posts it. You are not responsible for the network call.

## What NOT to do

- Do not run `schtasks` yourself — it's in the JSON.
- Do not re-check auth credentials — already in `facts.auth`.
- Do not spawn subagents or use `ToolSearch` — every turn costs quota. Target ≤6 tool calls total (1 Read, 1–2 Bash for version/post, and a couple of memory reads only if diagnosing an unknown disabled task).
- Do not treat a task in `offboarded_hints` as a failure even if it's disabled.
- Do not alert on remote/cloud triggers — they're archived.
