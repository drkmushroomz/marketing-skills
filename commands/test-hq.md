Run a smoke test against all Jetfuel HQ MCP tools. Call each tool with minimal valid arguments and report pass/fail.

## Test Plan

Run these in order. For tools that require IDs, use values from previous responses.

### Phase 1: People (no dependencies)
1. `hq_get_my_profile` — no args
2. `hq_list_team` — no args
3. `hq_get_time_logs` — no args (defaults to current week)
4. `hq_get_time_summary` — no args
5. `hq_get_pto_balance` — no args
6. `hq_get_pto_requests` — no args
7. `hq_get_pay_rates` — no args

### Phase 2: Business (needs a client ID)
8. `hq_list_clients` — no args
9. Use the first client ID from step 8 for the rest:
10. `hq_get_client` — id from step 8
11. `hq_get_client_contacts` — client_id from step 8
12. `hq_get_client_goals` — client_id from step 8
13. `hq_get_client_time_summary` — client_id from step 8
14. `hq_list_projects` — client_id from step 8

### Phase 3: Marketing (needs platform ID)
15. `hq_get_client_platforms` — client_id from step 8
16. If platforms exist, use first platform_id:
17. `hq_list_campaigns` — platform_id from step 15
18. `hq_get_platform_insights` — platform_id from step 15
19. If Klaviyo platform exists:
20. `hq_list_email_campaigns` — platform_id
21. `hq_get_klaviyo_lists` — platform_id

### Phase 4: Ads (needs campaign ID)
22. If campaigns exist from step 17, use first campaign_id:
23. `hq_get_campaign_detail` — campaign_id
24. `hq_get_campaign_insights` — campaign_id
25. `hq_get_client_spend` — client_id from step 8
26. `hq_list_audits` — client_id from step 8
27. If audits exist: `hq_get_audit_detail` — audit_id
28. `hq_get_campaign_changelogs` — client_id from step 8

### Phase 5: Utilities
29. `hq_sync_preferences` — context: "smoke_test"
30. `hq_check_updates` — no args

## Output Format

After running all tests, display results as:

```
Jetfuel HQ Smoke Test Results
═══════════════════════════════

Phase 1: People
  hq_get_my_profile          PASS  (120ms)
  hq_list_team               PASS  (95ms)
  ...

Phase 2: Business
  hq_list_clients            PASS  (110ms)
  ...

Phase 3: Marketing
  hq_get_client_platforms    PASS  (88ms)
  hq_list_campaigns          SKIP  (no platforms found)
  ...

Phase 4: Ads
  ...

Phase 5: Utilities
  hq_sync_preferences        PASS  (150ms)
  hq_check_updates           PASS  (90ms)

═══════════════════════════════
Summary: 25/27 PASSED, 0 FAILED, 2 SKIPPED
```

Mark as SKIP (not FAIL) if a tool can't be tested because a dependency returned no data (e.g., no campaigns exist). Only mark FAIL if the tool returns an error when called with valid inputs.
