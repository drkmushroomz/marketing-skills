---
name: linkedin-enrich
description: Enrich a list of contacts with current LinkedIn data. Use when the user wants to verify contact info, check if leads changed jobs, pull current titles/companies, or enrich a spreadsheet of prospects with LinkedIn profile data. Also use when the user mentions "LinkedIn enrichment," "check their LinkedIn," "verify these contacts," "did they change jobs," "enrich leads," "LinkedIn lookup," or "pull LinkedIn profiles." Works with Google Sheets, CSV files, or inline lists.
metadata:
  version: 1.0.0
---

# LinkedIn Profile Enrichment

Enrich contacts with current LinkedIn data using the Apify MCP server. Cross-references web research to catch job changes, company pivots, and stale data before outreach.

## Prerequisites

- Apify MCP server must be connected (`claude mcp list` should show `apify: Connected`)
- Free tier ($5/mo) supports ~1,250 direct profile lookups or ~50 search-based lookups

## Two Scraping Modes

### Mode A: Direct URL Scraper (PREFERRED -- $0.004/profile)

**Actor:** `harvestapi/linkedin-profile-scraper`

Use when you have LinkedIn URLs or public identifiers. 100% hit rate.

```
Input:
  - profileScraperMode: "Profile details no email ($4 per 1k)"
  - urls: ["https://www.linkedin.com/in/username1", ...]
  OR
  - publicIdentifiers: ["username1", "username2", ...]
```

**How to get URLs:** Web search each contact first (e.g., "Clara Veniard Coro Foods LinkedIn") to find their profile URL. Collect all URLs, then scrape in one batch call.

### Mode B: Search Scraper (BACKUP -- $0.10+/profile)

**Actor:** `harvestapi/linkedin-profile-search`

Use when you only have names and companies. ~30% hit rate on less prominent profiles.

```
Input:
  - searchQuery: "FirstName LastName Company"
  - profileScraperMode: "Full"
  - maxItems: 1
```

**Warning:** Charges $0.10 per search page even for 0-result queries. Budget ~50 lookups max on the free tier via this method.

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Load contact list
- [ ] Step 2: Collect LinkedIn URLs (web search)
- [ ] Step 3: Batch scrape via Apify
- [ ] Step 4: Compare and flag changes
- [ ] Step 5: Update source (sheet/CSV) with corrections
```

### Step 1: Load Contact List

Accept contacts from:
- **Google Sheet:** Read with `read_sheet_values` (always specify a range)
- **CSV file:** Read from local file
- **Inline list:** User pastes names + companies

Extract: Name, Company, Title, Email (if available)

### Step 2: Collect LinkedIn URLs

For each contact, run a web search to find their LinkedIn profile URL:
- Search: `"FirstName LastName" "Company" site:linkedin.com/in`
- Fallback: `"FirstName LastName" LinkedIn`

**Parallelize with agents** -- launch 4-5 search agents, each handling ~10 contacts.

Collect results as: `{name, linkedin_url, search_note}`

### Step 3: Batch Scrape via Apify

**If you have URLs (Mode A):**

Call `harvestapi/linkedin-profile-scraper` with all URLs in one batch:

```json
{
  "profileScraperMode": "Profile details no email ($4 per 1k)",
  "urls": ["url1", "url2", "url3", ...]
}
```

Then fetch output with fields: `firstName,lastName,headline,linkedinUrl,location.linkedinText,currentPosition,about,experience`

**If you only have names (Mode B):**

Call `harvestapi/linkedin-profile-search` individually per contact. Run up to 6 in parallel.

### Step 4: Compare and Flag Changes

For each contact, compare the original data against LinkedIn:

| Check | Flag If |
|-------|---------|
| Current company | Different from original company in the list |
| Current title | Different from original title |
| Location | Moved to a new city/region |
| Headline | Contains new venture, "Founder of...", "Looking for..." |
| About section | Mentions new projects, pivots, or interests |

Output a change report:

```
CHANGES DETECTED:
- Jane Doe: Was VP Marketing at OldCo → Now CMO at NewCo (since Jan 2026)
- John Smith: Confirmed still at SameCo, title unchanged
- Bob Lee: Profile not found (may be private or deleted)
```

### Step 5: Update Source

Write corrections back to the source:
- **Google Sheet:** Use `modify_sheet_values` to update relevant cells
- **CSV:** Overwrite the file with corrected data
- **Inline:** Display the corrected list

## Useful Output Fields

| Field | What It Contains |
|-------|------------------|
| `firstName`, `lastName` | Full name |
| `headline` | Current title/tagline |
| `linkedinUrl` | Profile URL (save for future lookups) |
| `location.linkedinText` | Location string |
| `currentPosition` | Array of current roles (company, start date) |
| `about` | Bio/summary text |
| `experience` | Full work history with dates |
| `education` | Schools and degrees |
| `skills` | Skill endorsements |
| `followerCount` | Network size signal |
| `connectionsCount` | Connection count |

## Cost Budgeting

| Method | Cost Per Profile | Profiles per $5 |
|--------|-----------------|-----------------|
| Direct URL scraper | $0.004 | ~1,250 |
| Search scraper | $0.104 | ~48 |
| Search (0 results) | $0.10 | ~50 |

Always prefer Mode A. The extra step of web-searching for URLs pays for itself 25x in credit savings.

## Error Handling

| Error | Fix |
|-------|-----|
| `0 results` from search | Profile is private or name is too generic. Try web search for URL instead. |
| `403 / profile can't be accessed` | Profile is restricted. Skip and note. |
| `APIFY_TOKEN` errors | Run `claude mcp list` to check connection. Re-add if needed. |
| Credits exhausted | Wait for monthly reset or upgrade to $29/mo Starter plan. |
