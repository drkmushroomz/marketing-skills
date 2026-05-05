# Search Term Audiences

Build custom audience segments from search intent data for Google Ads Demand Gen campaigns.

<role>
You are a paid media strategist building search term custom audiences for Demand Gen campaigns. You combine Google Ads search data, brand intelligence, and competitive context to create high-intent audience segments that drive efficient conversions on YouTube, Discover, and Gmail placements.
</role>

<task>
Analyze a brand's search landscape across multiple data sources, generate themed audience segments following the Search-to-Signal methodology, review with the user, then create the custom audiences in Google Ads.
</task>

## Setup

1. Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
2. Read `.claude/ops/search-term-audiences/config.json` for account list and settings.
3. Resolve the target account from `$ARGUMENTS`:
   - If a known account slug, use it.
   - If empty or unrecognized, list available accounts and ask.
4. Parse flags from `$ARGUMENTS`:
   - `--dry-run` — run Phases 1-3 only (no audience creation). This is the DEFAULT.
   - `--create` — run all 4 phases including audience creation in Google Ads.
   - `--refresh` — regenerate segments for an account that already has audiences.
   - `--phase <N>` — start at a specific phase (for resuming).

## Phase 1: Gather Brand Intelligence

Collect data from all available sources. Run these in parallel where possible.

### 1a. Load client brief
Read the `client_brief` file from config (e.g., `.claude/skills/ad-copy-analyzer/client-briefs/barker-wellness.md`). Extract:
- Product portfolio (SKUs, categories, hero products)
- Target audience personas and psychographics
- Competitive landscape
- Brand voice and content pillars
- Known problem-solution angles

### 1b. Pull Google Ads search term data
Use `gads_list_search_terms` with the account's `customer_id` and `lookback_days` from config. Request maximum rows. This gives actual search queries with:
- Impressions, clicks, conversions, cost
- The campaigns and ad groups they triggered

Also pull:
- `gads_list_keywords` — current keyword structure to understand targeting gaps
- `gads_list_campaigns` — campaign types and structure (identify existing Demand Gen campaigns)

### 1c. Check existing custom audiences
Use `gads_list_custom_audiences` to get all current custom audiences. Flag any that:
- Already match a theme we'd create (dedup)
- Have names following our naming convention ("Search Intent - ...")
- If `--refresh` flag is set, note these for replacement

### 1d. Gather communication context
Pull recent brand context from communication channels. These are OPTIONAL — skip gracefully if a source is unavailable or returns no results.

**Slack** (if `slack_channel` in account config):
- Use Slack `conversations_history` on the account's channel (last 30 days)
- Look for: strategy discussions, product launches, competitor mentions, performance concerns, new angles to test

**Email** (search Gmail):
- Use `search_gmail_messages` with query: `"{account_label}"` limited to last 30 days
- Look for: client meeting recaps, strategy shifts, new product announcements, competitive intelligence

**Google Drive** (search for transcripts):
- Use `search_drive_files` with query: `"{account_label}" type:document`
- Look for: meeting transcripts, strategy documents, campaign briefs

**Jetfuel HQ**:
- Use `hq_get_client` and `hq_list_campaigns` for the account
- Look for: campaign structure, active initiatives, recent changelogs

### 1e. Synthesize intelligence
Compile a brief intelligence summary (DO NOT output this to user yet):
- Key product categories and their relative importance
- Known competitors and their positioning
- Active pain points and solution angles
- Recent strategic shifts or new opportunities from comms
- Gaps in current keyword/audience coverage

---

## Phase 2: Generate Audience Segments

For each theme type in `theme_priority_ecomm` order from config, generate candidate segments.

### Rules (enforced for ALL segments):
- **Naming**: Follow `naming_convention` from config: `"Search Intent - {Theme Name}"`
- **Term count**: Each segment should have `terms_per_segment.min` to `terms_per_segment.max` keywords
- **No mixing**: NEVER include competitor terms in category segments or vice versa
- **Use real language**: Prefer actual search terms from the Google Ads report over invented phrases
- **Variant inclusion**: Include common misspellings, plural/singular, word order variations
- **One segment per product category**: Don't over-bundle unrelated products into one segment

### Theme generation logic:

#### 1. Product/Category
For each entry in `product_categories` from config:
- Find all matching search terms from the Google Ads report
- Expand with natural variations (plural, singular, with/without brand modifier)
- Group tightly related terms (e.g., "bath salts" + "soaking salts" + "mineral bath soak")
- Create one segment per distinct product category
- Name: `"Search Intent - {Category Name}"` (e.g., "Search Intent - Tattoo Aftercare")

#### 2. Competitor
For each competitor in config:
- Include: brand name, domain, brand + product combos, brand + review
- Group competitors by category if they compete in the same space
- Can create one segment per competitor OR one per competitor category
- Name: `"Search Intent - Competitor - {Name}"` (e.g., "Search Intent - Competitor - Mad Rabbit")

#### 3. Problem/Solution
Cross-reference client brief pain points with search term patterns:
- "how to heal...", "natural remedy for...", "best way to relieve..."
- Group by problem theme (e.g., sleep, recovery, energy, skin care)
- Name: `"Search Intent - {Problem Theme}"` (e.g., "Search Intent - Sleep & Relaxation")

#### 4. Comparison/Review
Find search terms with comparison signals:
- "best {category}", "{product} vs {product}", "{product} review", "{category} 2026"
- Group by category
- Name: `"Search Intent - Reviews - {Category}"`

#### 5. Long-Tail Purchase
Find search terms with transactional signals:
- "buy {product} online", "{product} coupon", "{product} discount", "{product} free shipping", "{product} subscription"
- Can combine across product categories if volume is low
- Name: `"Search Intent - Purchase Intent - {Category}"`

#### 6. Research Intent
Find informational search terms:
- "what is {ingredient}", "{product} benefits", "how to use {product}", "{ingredient} side effects"
- Group by topic cluster
- Name: `"Search Intent - Research - {Topic}"`

#### 7. Seasonal/Event
Only create if seasonal patterns are evident in the data:
- Holiday-related, seasonal wellness trends, event-driven
- Name: `"Search Intent - Seasonal - {Event}"`

### Post-generation checks:
- Remove any segment with fewer than `terms_per_segment.min` keywords
- Flag segments that may have low combined search volume (use impressions as proxy: if total impressions across all terms < 1000 over the lookback period, flag it)
- Verify no competitor terms leaked into category segments
- Check for duplicate terms across segments (some overlap is OK but flag heavy duplication)

---

## Phase 3: Review with User

Present the proposed segments for approval.

### Output format:

#### Summary
> Found {N} audience segments across {M} themes for {Account Label}.
> Data sources: Google Ads ({X} search terms), client brief, {other sources used}.

#### Segment Table
For each segment, display:

```
### {Segment Name}
**Theme:** {theme_label} | **Terms:** {count} | **Est. Impressions:** {total}

Keywords:
{keyword1}, {keyword2}, {keyword3}, ... {all keywords}

**Rationale:** {why this segment, what data supported it}
```

#### Warnings
- Flag segments below the volume threshold
- Note existing audiences that overlap (from Phase 1c dedup check)
- Highlight any segments where terms were mostly invented (not from search data)

#### Action prompt
If `--dry-run` (default):
> These segments are ready to create. Run `/search-term-audiences {account} --create` to build them in Google Ads.
> Or modify the segments above and I'll adjust before creating.

If `--create`:
> Review the segments above. Reply **go** to create all, or tell me which to modify/skip.

---

## Phase 4: Create in Google Ads

Only runs with `--create` flag and user confirmation.

### For each approved segment:
1. Call `gads_create_custom_audience` with:
   - `customer_id` from config
   - `name` = the segment name
   - `keywords` = the full keyword list
   - `description` = "{theme_label} audience for {account_label}. {keyword_count} search terms. Created {date}."
2. Wait for response before creating the next (sequential, not parallel)
3. Track successes and failures

### Post-creation:
1. **Report results** to user:
   ```
   ### Created Audiences
   | Segment | ID | Keywords | Status |
   |---|---|---|---|
   | Search Intent - Tattoo Aftercare | 123456 | 22 | Created |
   ```

2. **Post to Slack** (if `slack_channel` in config):
   Post a summary to the account's Slack channel:
   > Search Term Audiences created for {Account Label}:
   > - {Segment 1} ({N} terms)
   > - {Segment 2} ({N} terms)
   > ...
   > Next step: Attach these audiences to Demand Gen campaigns.

3. **Next steps guidance**:
   > **To use these audiences:**
   > 1. Open Google Ads > Campaigns > your Demand Gen campaign
   > 2. Go to the asset group > Audience signals
   > 3. Add custom segments > search for "Search Intent"
   > 4. Select the audiences you want to test
   > 5. Disable "Optimized targeting" initially to preserve precision
   > 6. Allow 2-4 weeks learning phase before optimizing

---

## Error Handling

- If Google Ads API returns an error for audience creation, log the error and continue with remaining segments. Report all failures at the end.
- If a data source (Slack, Gmail, Drive) is unavailable, skip it and note in the summary which sources were used.
- If the account has no search term data (new account), rely more heavily on the client brief and config product_categories to generate segments. Note that these are "seed" audiences that should be refined after 90 days of search data.
- If `gads_list_custom_audiences` fails (API version issue), skip dedup check and warn the user to manually verify no duplicates exist.

## Constraints

- NEVER create audiences without explicit user approval (Phase 3 gate)
- NEVER mix competitor terms into category segments
- NEVER include brand terms (the client's own brand) in audience segments -- these users already know the brand
- Default to `--dry-run` if no flag specified
- Sequential audience creation (one at a time) to avoid rate limits
