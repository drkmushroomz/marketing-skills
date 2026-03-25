---
name: search-term-miner
description: Auto-promote converting search terms to keywords — finds L7D converters not in account, adds exact + broad at staggered bids
disable-model-invocation: true
---

# Search Term Miner

Automatically finds converting search terms from the last 7 days that are missing as keywords and adds them with both exact match and broad match at staggered bids.

## Arguments

The user may specify:
- `--account <alias>` to run for a specific account (default: all accounts in config)
- `--dry-run` to preview without making changes
- `--lookback <days>` to override the default 7-day window

## Steps

1. **Load config:** Read `.claude/ops/search-term-miner/config.json` for account settings (customer IDs, default ad groups, bid levels).

2. **Get today's date** via shell command (`date`).

3. **Run the miner script:**

   ```bash
   cd "$CLAUDE_PROJECT_DIR"
   python .claude/ops/search-term-miner/search_term_miner.py [args]
   ```

   The script will:
   - Pull all search terms with 1+ conversions in the last 7 days
   - Fetch all existing keywords in the account
   - Identify gaps (converting terms missing as exact and/or broad keywords)
   - Add missing keywords into the same ad group the search term matched in
   - Exact match gets the higher bid, broad match gets the lower bid
   - Post a summary to Slack
   - Save state to `state.json`

4. **Report results** to the user:
   - How many converting search terms were found
   - How many were already covered
   - How many keywords were added (and which ones)
   - Any errors

## Config

Located at `.claude/ops/search-term-miner/config.json`:

```json
{
  "accounts": {
    "train-with-dave": {
      "customer_id": "9099081672",
      "default_ad_group_id": "193334888799",
      "exact_bid": 1.50,
      "broad_bid": 0.75
    }
  },
  "lookback_days": 7,
  "min_conversions": 1,
  "dry_run": false
}
```

## Important Rules

- Always run with `--dry-run` first if the user hasn't explicitly asked for live mode
- The script adds keywords to the SAME ad group the search term originally matched in
- Exact match bid should always be higher than broad match bid
- Never add branded competitor terms — flag them for manual review
- State is saved to `state.json` to avoid re-adding the same terms on subsequent runs
