# SEO Keyword Planner

Build a comprehensive organic keyword target list for any client site. Combines GSC data, competitive research, and site structure analysis into a prioritized Google Sheet.

## When to Use

When the user wants to build a keyword strategy, identify target keywords, find content gaps, or create an SEO keyword plan for a site.

## Arguments

The user may specify:
- A site domain (e.g., "brightheadstart.com")
- A GSC alias from `mcp-servers/google-search-console/config.json`
- `--refresh` to update an existing keyword sheet with fresh GSC data
- `--sheet <url>` to update an existing sheet instead of creating a new one

## Steps

1. **Load identity and config:**
   - Read `.claude/me.md` for user identity.
   - Read `mcp-servers/google-search-console/config.json` for site mappings.

2. **Pull GSC data (if available):**
   - Top queries (90 days, limit 25)
   - Top pages (90 days, limit 25)
   - Query + page combinations (90 days, limit 25)
   - Note: GSC has ~3 day lag. If the site is new, data may be minimal.

3. **Analyze site structure:**
   - Fetch the sitemap to understand page types and URL patterns
   - Identify existing page templates (city pages, service pages, school pages, etc.)
   - Map keyword clusters to existing URL patterns

4. **Research keyword universe:**
   Use WebSearch to research keywords across these clusters:
   - **[Service] + [City]** combos (primary commercial intent)
   - **Best/top + [service] + [location]** (commercial comparison)
   - **[Service type] + [location]** (montessori, bilingual, etc.)
   - **Cost/pricing queries** (informational, high conversion)
   - **Informational guides** (how-to, vs, checklist queries)
   - **Long-tail / modifier queries** (age-specific, schedule, features)
   - **Near me / ZIP code** queries
   - **Seasonal queries** (enrollment, summer camp)
   - **Brand terms**

5. **Build the Google Sheet with 3 tabs:**

   ### Tab 1: Target Keywords
   | Keyword | Cluster | Intent | Target Page | Priority | Est. Volume | GSC Position | GSC Impressions | Notes |

   - Minimum 100 keywords, ideally 150+
   - Group by cluster for easy filtering
   - Intent: Commercial, Informational, Transactional, Navigational
   - Priority: High (volume + relevance), Medium, Low
   - Est. Volume: Use research estimates. Flag "Needs KW Planner" where uncertain.
   - Include GSC position/impressions where data exists

   ### Tab 2: GSC Current Data
   | Page | Clicks | Impressions | CTR | Avg Position | Status |

   - All pages with any GSC impressions
   - Status column flags: "Page 1", "Almost page 1", "Needs optimization"

   ### Tab 3: Content Gaps
   | Content Gap | Why It Matters | Suggested URL | Target Keywords | Priority |

   - Pages that should exist but don't
   - High-volume keywords with no matching page
   - Service verticals not yet covered
   - Guide/blog content opportunities

6. **Format the sheet:**
   - Bold + colored header rows
   - Freeze row 1 on all tabs

7. **Present summary to user:**
   - Total keywords mapped
   - Keyword clusters identified
   - Top 5 highest-priority gaps
   - Whether Google Keyword Planner or Ahrefs would add value (and for what specifically)

## Important Rules

- Always use `limit: 25` on GSC tool calls to prevent context overflow
- Est. Volume is directional, not exact. Flag where Keyword Planner data would improve accuracy.
- Map every keyword to an existing or proposed target page -- no orphan keywords
- Prioritize keywords where the site already has a page template (city pages, service pages)
- For new sites with thin GSC data, lean heavier on research and site structure analysis
- Format CTR as percentage, position to 1 decimal
- Include competitive notes where relevant (e.g., "dominated by Yelp", "low competition")
