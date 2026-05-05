---
name: audience-audit
description: Audit a Google Ads account for missing remarketing audiences, with actionable build instructions for each gap
disable-model-invocation: true
---

# Audience Audit

Audit a Google Ads account's audience coverage against a defined checklist of remarketing audiences. Identifies gaps and provides build instructions for each missing audience.

## Arguments

The user may specify:
- An account name (e.g., "barker-wellness", "train-with-dave"). Default: ask.
- `--all` to audit all accounts in config.

## Steps

1. **Load identity and config:**
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/ops/audience-audit/config.json` for account mappings and audience definitions.

2. **Run the auditor script:**

   For a single account:
   ```bash
   python .claude/ops/audience-audit/audience_auditor.py --account {account}
   ```

   For all accounts, run once per account key in config.json.

   Parse the JSON output. If an error is returned, show it and stop.

3. **Present the audit report:**

   ### Audience Audit: {label} ({account_type})

   **Coverage: {coverage_pct}%** — {total_matched}/{total_defined} audiences found

   | Priority | Found | Missing |
   |----------|-------|---------|
   | Critical | {n} | {n} |
   | High | {n} | {n} |
   | Medium | {n} | {n} |
   | Low | {n} | {n} |

4. **Show gaps by priority (critical first):**

   For each gap:

   #### ❌ {name} ({priority})
   {description}

   **How to build:**
   {build_method}

   **Alternative method:**
   {alt_method} *(if not null)*

5. **Show matched audiences:**

   For each match:

   #### ✅ {name} ({priority})
   | List Name | Search Size | Display Size |
   |-----------|-------------|--------------|
   | {existing list name} | {size} | {size} |

6. **Show unmatched lists** (audiences that exist in the account but don't match any definition):

   If there are unmatched lists, show them under:
   ### Other Audiences in Account
   These audiences exist but don't match any checklist item. Review whether they're still useful or should be removed.
   - {name} — {type} — Search: {size}, Display: {size}

7. **Summary and next steps:**
   - Total coverage percentage
   - Count of critical gaps (these should be built first)
   - Quick wins: audiences that can be built with just GA4 (vs. needing Shopify/Klaviyo exports)
   - Ask: "Want me to create a ClickUp task for each missing audience?" or "Want me to run this for another account?"

## Notes
- Critical audiences should always exist — flag these prominently
- For ecomm accounts: purchasers, abandoned cart, product page viewers, and repeat purchasers are table stakes
- For awareness accounts: all site visitors, engaged visitors, and store locator visitors are table stakes
- Size of 0 may mean the audience was just created or the tag isn't firing — flag this
- Audiences with very small sizes (<100) may not be eligible for targeting — note this
- Match is case-insensitive and uses substring matching against the match_keywords in config
