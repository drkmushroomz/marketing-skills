---
name: search-term-miner
description: Find converting search terms missing from PPC accounts, score each for quality vs random luck, suggest or auto-add strong ones, notify on Slack
disable-model-invocation: true
---

# Search Term Miner

Finds converting search terms not yet in the account, scores each for quality (strong / review / skip), and either suggests them for human review or auto-adds the strong ones. Posts results to Slack.

## Arguments

The user may specify:
- `--account <alias>` to run for a specific account (default: all accounts in config)
- `--add` to add "strong" terms to the account (default: suggest only)
- `--add --include-review` to also add "review" terms
- `--lookback <days>` to override the default 7-day window
- `--dry-run` legacy flag, same as suggest mode

## Steps

1. **Load config:** Read `.claude/ops/search-term-miner/config.json` for account settings.

2. **Get today's date** via shell command (`date`).

3. **Run the miner script:**

   ```bash
   cd "$CLAUDE_PROJECT_DIR"
   python .claude/ops/search-term-miner/search_term_miner.py [args]
   ```

   The script will:
   - Pull all search terms with 1+ conversions in the lookback window
   - Fetch all existing keywords in the account
   - Identify gaps (converting terms missing as exact and/or broad keywords)
   - **Score each gap term** for quality using these signals:
     - Conversion volume (1 conv = weak, 3+ = good, 5+ = high confidence)
     - Conversion rate vs reasonable thresholds
     - CPA vs account average CPA (fetched automatically)
     - Click volume (statistical confidence)
     - CTR (intent signal)
     - Query length (single word = too broad, 7+ words = ultra long-tail)
     - Word overlap with existing keywords (on-theme vs off-theme)
   - **Classify** each term:
     - **strong** (score 55+) — safe to add, clear pattern
     - **review** (score 30-54) — plausible but needs human judgement
     - **skip** (score <30) — likely noise, random luck, or bad fit
   - In `--add` mode: add strong terms as exact + broad at staggered bids
   - Post scored report to Slack (channel + DM)
   - Save state to `state.json`

4. **Report results** to the user:
   - Scored list grouped by classification (strong / review / skip)
   - Each term shows: score, conversions, CVR, CPA, match types needed, reasons
   - Account average CPA for context
   - How many keywords were added (if --add mode)
   - Any errors

## Quality Scoring — What Makes a "Good" vs "Bad" Keyword

The scoring engine evaluates each converting search term on a 0-100 scale:

| Signal | Strong positive | Weak / negative |
|--------|----------------|-----------------|
| Conversions | 5+ (high confidence) | 1 (could be noise) |
| CVR | 15%+ (excellent) | <4% with data |
| CPA | Below account avg | >1.5x account avg |
| Clicks | 20+ (solid data) | <3 (thin data) |
| CTR | 8%+ (high intent) | <2% at 50+ impr |
| Query length | 2-3 words (sweet spot) | 1 word (too broad) or 7+ (won't scale) |
| Theme match | High word overlap with existing KWs | No overlap (off-theme, random) |

A term with 1 conversion, 2 clicks, high CPA, and no overlap with existing keywords = **skip** (random luck). A term with 4 conversions, 12% CVR, CPA below average, and words matching your existing theme = **strong**.

## Scheduling

To run weekly on autopilot:
- Use `/schedule` to create a cron trigger
- Suggest mode notifies on Slack for review
- Add `--add` to the schedule for hands-off promotion of strong terms

## Config

Located at `.claude/ops/search-term-miner/config.json`:

```json
{
  "mcc_id": "1874174744",
  "accounts": {
    "train-with-dave": {
      "customer_id": "9099081672",
      "label": "Train with Dave",
      "default_ad_group_id": "193334888799",
      "exact_bid": 1.50,
      "broad_bid": 0.75
    }
  },
  "lookback_days": 7,
  "min_conversions": 1,
  "slack_channel": "C0AMKEKU9ND",
  "slack_dm": {
    "train-with-dave": ["U4DMWG4HX"]
  }
}
```

## Important Rules

- Default mode is **suggest** — never auto-add without `--add` flag
- The script adds keywords to the SAME ad group the search term originally matched in
- Exact match bid should always be higher than broad match bid
- Never add branded competitor terms — flag them for manual review
- "skip" terms are NEVER added, even with `--add --include-review`
- State is saved to `state.json` to avoid re-adding the same terms on subsequent runs
- Slack notifications fire in both suggest and add modes
