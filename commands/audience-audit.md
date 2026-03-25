# Audience Audit

Audit a PPC account's audience lists against best-practice audience definitions and identify gaps.

## Arguments

- `$ARGUMENTS` — optional: account slug (e.g. `barker-wellness`) or `all` to run across all accounts. If empty, ask which account.

## Steps

1. **Load config:**
   - Read `.claude/ops/audience-audit/config.json` for account list and audience definitions.
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.

2. **Resolve which account(s) to audit:**
   - If `$ARGUMENTS` is a known account slug, audit that one.
   - If `$ARGUMENTS` is `all`, audit every account in config.
   - If `$ARGUMENTS` is empty or unrecognized, list available accounts and ask the user to pick.

3. **For each account, pull existing audiences from Google Ads:**
   - Use `gads_query` with customer_id from config:
     ```
     SELECT user_list.name, user_list.type, user_list.size_for_display, user_list.size_for_search, user_list.membership_status, user_list.match_rate_percentage FROM user_list ORDER BY user_list.name
     ```
   - Parse the results. An audience is **active** if `membership_status = OPEN` AND (`size_for_display > 0` OR `size_for_search > 0`). Otherwise it's **inactive/empty**.

4. **Match existing audiences against definitions:**
   - Use the account's `type` field (`ecomm` or `awareness`) to select the right audience definitions from config.
   - For each definition, check if ANY existing user_list name (case-insensitive) contains any of the `match_keywords`.
   - Mark each definition as: ✅ **Active** (matched + active), ⚠️ **Exists but empty/closed** (matched but inactive), or ❌ **Missing** (no match).

5. **Generate the audit report:**

   Output as markdown with these sections:

   ### {Account Label} — Audience Audit

   **Summary:** X of Y audiences active, Z missing.

   #### ✅ Active Audiences
   Table: Audience Name (from config) | Matched List Name (from Google Ads) | Display Size | Search Size | Source Type

   #### ⚠️ Exists but Empty/Closed
   Table: Audience Name | Matched List Name | Status | Recommendation (reactivate, rebuild, etc.)

   #### ❌ Missing Audiences
   Table, sorted by priority (critical → high → medium → low):
   - Audience Name | Priority | How to Build (from `build_method`) | Alt Method (from `alt_method` if available)

   #### 🎯 Top 3 Priorities
   Pick the top 3 missing or broken audiences by priority and impact. One sentence each explaining why this matters for this specific account.

6. **Offer next steps:**
   After the report, ask:
   > Want me to build any of these audiences? Customer Match lists I can upload via the API. GA4 audiences need to be created in the GA4 UI — I can give you step-by-step instructions for those.

7. **If running `all` accounts:**
   - Run steps 3-5 for each account sequentially.
   - After all accounts, add a **Cross-Account Summary** section:
     - Table: Account | Active | Missing | Top Gap
     - Call out any audience that's missing across ALL accounts (systemic gap).
