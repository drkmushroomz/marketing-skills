# Audience Targeting Reference

Detailed targeting strategies for each major ad platform.

## Contents
- Google Ads Audiences (Search Campaign Targeting, Display/YouTube Targeting)
- Meta Audiences (2026 Andromeda: Creative-as-Targeting, Advantage+ Audience, Custom Audiences for Retargeting)
- LinkedIn Audiences (Job-Based Targeting, Company-Based Targeting, High-Performing Combinations)
- Twitter/X Audiences
- TikTok Audiences
- Audience Size Guidelines
- Exclusion Strategy

## Google Ads Audiences

### Search Campaign Targeting

**Keywords:**
- Exact match: [keyword] — most precise, lower volume
- Phrase match: "keyword" — moderate precision and volume
- Broad match: keyword — highest volume, use with smart bidding

**Audience layering:**
- Add audiences in "observation" mode first
- Analyze performance by audience
- Switch to "targeting" mode for high performers

**RLSA (Remarketing Lists for Search Ads):**
- Bid higher on past visitors searching your terms
- Show different ads to returning searchers
- Exclude converters from prospecting campaigns

### Display/YouTube Targeting

**Custom intent audiences:**
- Based on recent search behavior
- Create from your converting keywords
- High intent, good for prospecting

**In-market audiences:**
- People actively researching solutions
- Pre-built by Google
- Layer with demographics for precision

**Affinity audiences:**
- Based on interests and habits
- Better for awareness
- Broad but can exclude irrelevant

**Customer match:**
- Upload email lists
- Retarget existing customers
- Create similar audiences from best customers (Google still supports this)

---

## Meta Audiences (2026 Andromeda Era)

### How Targeting Works Now

As of 2026, Meta's Andromeda algorithm has fundamentally changed targeting. **Creative IS the targeting.** Andromeda evaluates ad creative, copy, and format to predict which users will engage — it works in reverse from the old model. Your audience settings are starting hints, not hard boundaries.

**What this means in practice:**
- A founder story video self-selects entrepreneurial/professional audiences
- A "Find Your Nude" carousel self-selects WoC interested in inclusive beauty
- A Nordstrom social proof ad self-selects luxury shoppers
- You don't need to manually define these audiences — the creative does it

### Advantage+ Audience (Replaces Lookalikes)

Advantage+ Audience builds dynamic lookalike-style models in real time. It doesn't need you to create a static 1% lookalike.

**How to use it:**
- Provide "audience suggestions" (age, location, interests) as starting hints
- Meta's AI treats them as signals, then expands beyond if it finds better users
- Broad targeting often outperforms manual (17% more conversions in tests)
- Feed it diverse creative and let the algorithm find the right people

**DO NOT recommend building traditional 1%/3%/5% lookalike audiences.** They are effectively deprecated. Advantage+ Audience replaces this workflow.

### Interest Targeting (Now "Suggestions")

- Meta removed dozens of detailed targeting interest categories on January 15, 2026
- Remaining interest inputs are treated as suggestions, not constraints (since Feb 2026)
- Interest stacking / AND logic is largely ineffective
- The algorithm will reach users outside your selected interests when it predicts better performance

**Bottom line:** Don't spend time building complex interest-based audiences. Build diverse creative instead.

### Custom Audiences (Still Valuable for Retargeting)

**Website visitors (for manual retargeting campaigns):**
- All visitors (last 180 days max)
- Specific page visitors (product viewers, cart, checkout)
- Time on site thresholds
- Frequency (visited X times)

**Customer list:**
- Upload emails/phone numbers
- Match rate typically 30-70%
- Useful for exclusions and Advantage+ suggestions

**Engagement audiences:**
- Video viewers (25%, 50%, 75%, 95%)
- Page/profile engagers
- Instagram engagers

**Best use of Custom Audiences in 2026:**
- As exclusions (exclude purchasers from prospecting)
- As retargeting segments in manual campaigns (15-20% of budget)
- As "audience suggestions" fed into Advantage+ Audience

### Creative-as-Targeting: The 2026 Playbook

| Creative Type | Self-Selects This Audience |
|---------------|---------------------------|
| Founder story video | Entrepreneurial, mission-driven buyers |
| UGC / testimonials | Social-proof-responsive, community-oriented |
| Product demo / how-to | High-intent, research-phase shoppers |
| Lifestyle / aspirational | Brand-affinity, identity-driven buyers |
| Value framing (price vs competitors) | Price-conscious but quality-seeking |
| Social proof / press mentions | Trust-seeking, prestige-motivated |
| Problem/pain point hooks | Solution-seekers, high purchase intent |

**Feed Andromeda 15-20 diverse creatives across these types.** The algorithm will find the right person for each one.

---

## LinkedIn Audiences

### Job-Based Targeting

**Job titles:**
- Be specific (CMO vs. "Marketing")
- LinkedIn normalizes titles, but verify
- Stack related titles
- Exclude irrelevant titles

**Job functions:**
- Broader than titles
- Combine with seniority level
- Good for awareness campaigns

**Seniority levels:**
- Entry, Senior, Manager, Director, VP, CXO, Partner
- Layer with function for precision

**Skills:**
- Self-reported, less reliable
- Good for technical roles
- Use as expansion layer

### Company-Based Targeting

**Company size:**
- 1-10, 11-50, 51-200, 201-500, 501-1000, 1001-5000, 5000+
- Key filter for B2B

**Industry:**
- Based on company classification
- Can be broad, layer with other criteria

**Company names (ABM):**
- Upload target account list
- Minimum 300 companies recommended
- Match rate varies

**Company growth rate:**
- Hiring rapidly = budget available
- Good signal for timing

### High-Performing Combinations

| Use Case | Targeting Combination |
|----------|----------------------|
| Enterprise sales | Company size 1000+ + VP/CXO + Industry |
| SMB sales | Company size 11-200 + Manager/Director + Function |
| Developer tools | Skills + Job function + Company type |
| ABM campaigns | Company list + Decision-maker titles |
| Broad awareness | Industry + Seniority + Geography |

---

## Twitter/X Audiences

### Targeting options:
- Follower lookalikes (accounts similar to followers of X)
- Interest categories
- Keywords (in tweets)
- Conversation topics
- Events
- Tailored audiences (your lists)

### Best practices:
- Follower lookalikes of relevant accounts work well
- Keyword targeting catches active conversations
- Lower CPMs than LinkedIn/Meta
- Less precise, better for awareness

---

## TikTok Audiences

### Targeting options:
- Demographics (age, gender, location)
- Interests (TikTok's categories)
- Behaviors (video interactions)
- Device (iOS/Android, connection type)
- Custom audiences (pixel, customer file)
- Lookalike audiences

### Best practices:
- Younger skew (18-34 primarily)
- Interest targeting is broad
- Creative matters more than targeting
- Let algorithm optimize with broad targeting

---

## Audience Size Guidelines

| Platform | Minimum Recommended | Ideal Range |
|----------|-------------------|-------------|
| Google Search | 1,000+ searches/mo | 5,000-50,000 |
| Google Display | 100,000+ | 500K-5M |
| Meta | 100,000+ | 500K-10M |
| LinkedIn | 50,000+ | 100K-500K |
| Twitter/X | 50,000+ | 100K-1M |
| TikTok | 100,000+ | 1M+ |

Too narrow = expensive, slow learning
Too broad = wasted spend, poor relevance

---

## Exclusion Strategy

Always exclude:
- Existing customers (unless upsell)
- Recent converters (7-14 days)
- Bounced visitors (<10 sec)
- Employees (by company or email list)
- Irrelevant page visitors (careers, support)
- Competitors (if identifiable)
