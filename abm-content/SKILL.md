---
name: abm-content
description: "Create account-based content that pulls specific prospects in. Use when the user wants to create content targeting specific leads, accounts, or industries based on prospect research. Also use when the user mentions 'ABM content,' 'account-based marketing,' 'pull strategy,' 'content for prospects,' 'attract leads,' 'thought leadership for prospects,' 'industry-specific content,' 'write something that would get [person] to reach out,' or 'content magnet for [company/vertical].' This is the pull counterpart to cold-email (push). For generic content strategy, see content-strategy. For direct outreach, see cold-email."
metadata:
  version: 1.0.0
---

# ABM Content — Pull Strategy

Create content specifically designed to attract target prospects inbound. Instead of reaching out to them (push), you publish content they'll find, share, or engage with -- then they come to you.

## Before Creating

**Load context:**

1. Read `.claude/me.md` for identity and voice
2. Read `.claude/edwin-tone-guide.md` if it exists -- voice bible
3. Check if prospect research already exists:
   - Google Sheets (HubSpot re-engagement pipeline or similar)
   - Memory files (project notes from prior research)
   - LinkedIn enrichment data from `/linkedin-enrich` runs

**Understand the input** (ask if not provided):

1. **Who are the targets?** -- Specific people, companies, or a vertical/persona
2. **What research do we have?** -- Job changes, company news, funding, product launches, industry trends
3. **What's the goal?** -- Get them to visit our site, engage on LinkedIn, reply to a DM, book a call
4. **What channels?** -- Blog, LinkedIn, both, other

---

## How It Works

Traditional content marketing targets keywords. ABM content targets people. The difference:

| Generic Content | ABM Content |
|----------------|-------------|
| "5 PPC Tips for Ecommerce" | "How CPG Brands Scaling from 200 to 1,000 Retail Doors Use Paid Media to Drive Shelf Velocity" |
| Targets a keyword | Targets Clara Veniard, Melissa Daulton, and every CPG founder in your pipeline |
| Broad audience | 10-50 specific people would find this directly relevant |
| SEO-first | Shareability-first, SEO as a bonus |

The content should be so specific to the prospect's situation that when they see it, they think: "This is exactly what I'm dealing with right now."

---

## Content Types (pick one or stack)

### 1. Industry Insight Post (LinkedIn)

**Best for:** Prospects who are active on LinkedIn
**Length:** 150-300 words
**Turnaround:** Fast (30 min to write, immediate publish)

Structure:
- Open with a specific, non-obvious observation about their industry
- Share a data point or trend they care about
- Connect it to a problem they're likely facing
- End with a point of view (not a pitch)

**Example targeting CPG brands expanding into retail:**
> 220+ retail doors sounds like a win until you realize distribution without velocity is just expensive shelf rent.
>
> We're seeing CPG brands hit a wall at the 200-500 store mark: great sell-in, flat sell-through. The ones breaking past it are doing three things differently with their digital spend...

**Tag/mention strategy:** Don't tag the prospect directly. Post the content, then share it with them in a DM or email: "Wrote something about [their exact situation]. Thought of you."

### 2. Blog Post / Long-Form Article

**Best for:** Capturing search intent + sharing with prospects
**Length:** 1,200-2,000 words
**Turnaround:** 2-4 hours including research

Structure:
- Title targets the prospect's exact situation (industry + growth stage + challenge)
- Opening paragraph describes their world so accurately they feel seen
- Body delivers genuine strategic value -- frameworks, data, examples
- Proof section uses anonymized Jetfuel case studies from similar verticals
- CTA is soft: "If this sounds familiar, we should talk"

**Topic formula:** `[Prospect's Industry] + [Their Growth Stage] + [The Challenge They're Facing]`

Examples from current pipeline research:
- "Retail Media for CPG Brands: How to Turn 220 Target Doors into Real Shelf Velocity" (targets Clara Veniard/Coro, Melissa Daulton/FoodStory)
- "Paid Media Playbook for DTC Supplement Brands Navigating Meta's Health Data Restrictions" (targets Rick Sliter/MedCline, Caroline Carralero/Daily Nouri, Tina Shim/Apothekary)
- "How Beauty Brands Scale DTC Revenue Past the First $5M" (targets Angela Cheung/Emdash, Una Cassidy/Tip Beauty, Andy Scully/cocokind)
- "Digital Marketing for Payment Technology Companies: From Trade Show Leads to Pipeline" (targets Gavin Means/ID Tech, Justin Ning/ID Tech, Bill Nichols/Datecs)

### 3. Mini Case Study / Results Snapshot

**Best for:** Prospects who are skeptical or data-driven
**Length:** 300-500 words or a single LinkedIn carousel
**Turnaround:** 1-2 hours

Structure:
- Situation: Anonymized company similar to the prospect ("A DTC skincare brand doing $2M/year...")
- Challenge: The exact problem the prospect likely faces
- What we did: 2-3 specific tactical changes
- Results: Hard numbers (anonymized but real)
- Implied message: "We've done this for someone just like you"

### 4. Industry Report / Data Drop

**Best for:** High-value prospects, C-suite, multiple targets in one vertical
**Length:** PDF or Google Doc, 5-10 pages
**Turnaround:** 1-2 days

Structure:
- Compile real data about the prospect's industry (market size, growth trends, competitive landscape)
- Add Jetfuel's point of view on what the data means
- Include benchmarks they can compare themselves against
- Gate it lightly (or share ungated on LinkedIn for maximum reach)

---

## Workflow

```
Task Progress:
- [ ] Step 1: Cluster prospects by vertical/situation
- [ ] Step 2: Pick content type and angle for each cluster
- [ ] Step 3: Research and draft
- [ ] Step 4: Quality check
- [ ] Step 5: Publish and distribute
```

### Step 1: Cluster Prospects by Vertical/Situation

Group target prospects who share a similar situation. One piece of content can pull multiple prospects.

**How to cluster:**
- Same industry (CPG, beauty, payments, cannabis, edtech)
- Same growth stage (scaling retail, launching DTC, entering new markets)
- Same challenge (Meta restrictions, retail velocity, B2B demand gen)

Read the prospect research (Google Sheet, memory, LinkedIn enrichment) and group them.

### Step 2: Pick Content Type and Angle

For each cluster, select the content type that best matches:

| Cluster Size | Best Content Type |
|-------------|-------------------|
| 1-2 prospects | LinkedIn post (fast, personal) |
| 3-5 prospects | Blog post (targeted but scalable) |
| 5-10 prospects | Blog post + LinkedIn post promoting it |
| 10+ in same vertical | Industry report or data drop |

**Angle selection:** The angle should come from the prospect research. Use the specific things you found:
- Company milestones (funding, expansion, product launch)
- Industry trends affecting them
- Challenges visible from their hiring, reviews, or public statements
- Competitor moves that create pressure

### Step 3: Research and Draft

**For blog posts, use the write-content skill workflow** -- load Edwin's voice, pull case study data, research competitive landscape. The difference is you're writing for a named audience of 3-10 people, not a keyword.

**For LinkedIn posts, follow these rules:**
- Read `.claude/edwin-tone-guide.md` for voice
- No em dashes, no AI tells
- Open with a hook that speaks to the prospect's exact situation
- Keep it under 300 words
- End with a take, not a pitch

**For case studies:**
- Search Google Drive for real client data in the relevant vertical
- Anonymize everything per the confidentiality rules in write-content
- Lead with the result, then explain the how

### Step 4: Quality Check

Before publishing, verify:

- [ ] Would the target prospect read this and think "they get my business"?
- [ ] Does it deliver genuine value, not just thinly veiled self-promotion?
- [ ] Is every claim backed by real data (Jetfuel case studies or cited sources)?
- [ ] Does it read like Edwin wrote it, not a marketing AI?
- [ ] Zero em dashes, zero AI tells
- [ ] One clear next step (soft CTA, not "book a demo")

**The acid test:** If you removed Jetfuel's name from the piece, would it still be worth reading? If no, add more value.

### Step 5: Publish and Distribute

**Blog:** Use `/publish-blog` to push to jetfuel.agency as a draft
**LinkedIn:** Use `/social-content` conventions or draft in the social-content format
**Distribution to prospects:** After publishing, share the content with specific prospects:
- Email: "Wrote something about [their situation]. Thought you might find it useful." (use /cold-email voice)
- LinkedIn DM: Keep it to 2 sentences + link
- This bridges pull into push -- the content is the gift, the share is the nudge

---

## Push + Pull Coordination

This skill pairs with `/cold-email` and `/linkedin-enrich`:

| Skill | Role |
|-------|------|
| `/linkedin-enrich` | Research: who are they now, what are they doing |
| `/abm-content` | Pull: create content that attracts them inbound |
| `/cold-email` | Push: reach out directly with personalized outreach |

**Ideal sequence:**
1. Enrich contacts with LinkedIn data
2. Publish ABM content targeting their vertical/situation
3. Wait 1-2 days for organic visibility
4. Send cold email that references or links to the content

The cold email becomes 10x more credible when there's a relevant blog post or LinkedIn post backing it up. "We just published this analysis of [their industry]" is a stronger opener than "We help companies like yours."

---

## What to Avoid

- Writing content that's obviously a sales pitch disguised as thought leadership
- Generic advice that any agency could write ("test your ad creative" / "know your audience")
- Mentioning the prospect by name in the content (creepy, not flattering)
- Publishing content about an industry you have zero case study data in -- better to be honest about what you know
- Over-optimizing for SEO at the expense of specificity -- ABM content should feel like it was written for 10 people, not 10,000
