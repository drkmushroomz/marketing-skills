---
name: write-content
description: Write SEO + AIO optimized blog posts and pages for jetfuel.agency in Edwin's voice
disable-model-invocation: true
---

# Write Content

Write SEO and AIO-optimized content for jetfuel.agency — blog posts, service pages, and definition/explainer articles — in Edwin's authentic voice.

## Arguments

The user may specify:
- A **topic or title** (e.g., "Meta Health Ad Restrictions for Wellness Brands"). Required.
- A **content type**: `blog`, `service-page`, or `explainer`. Default: `blog`.
- A **target keyword** (e.g., "meta health ad restrictions 2026"). Optional — will be inferred from the topic if omitted.
- `--draft` to save as a Google Doc draft instead of outputting inline. Default: output inline.

## Steps

### Phase 0: Load Context

1. **Load identity and voice:**
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for user preferences.
   - Read `.claude/edwin-tone-guide.md` — this is the voice bible. The **Do's and Don'ts for Content Marketing** section and the **LinkedIn Post Writing Guide anti-patterns** apply directly to long-form content.

2. **Check for existing SEO research:**
   - If the topic matches something in the SEO Opportunities spreadsheet (`1-qOYW-5nzcKI7WTGLPiMLxRG99UxcCqax_aNe9TDLsQ`), read the relevant tabs to pull priority score, impressions, position, and recommended action.
   - Check the **LLM Visibility** and **SEO + LLM Overlap** tabs — if this topic was identified there, pull the specific LLM prompts it should answer and the competitors currently getting cited.

3. **Pull real data from case studies and client briefs:**
   - Search Google Drive for case studies: `name contains 'case study' AND mimeType = 'application/vnd.google-apps.document'`
   - Read any case studies relevant to the topic and extract verified metrics (ROAS changes, CPA, CTR, revenue growth, etc.)
   - These are published/approved numbers and can be used with client names if the case study is public
   - Also check `.claude/ops/ad-copy-analyzer/client-briefs/` for additional client context
   - Case study data is the gold standard for content. Always prefer it over transcript data or external benchmarks.

4. **Mine meeting transcripts for real-world insights:**
   - Search Google Drive for transcripts related to the topic:
     - `mcp__google-workspace__search_drive_files` with topic keywords, platform names, and tactic names
     - Also search for `"Notes by Gemini"` transcripts from huddles and kick-offs
     - Check `.claude/ops/ad-copy-analyzer/client-briefs/` for any existing client briefs with relevant data
   - Read matching transcripts using `get_doc_as_markdown` (batch up to 5 in parallel).
   - Extract and tag anything usable for content:
     - **Anonymized results** — ROAS changes, CPA drops, conversion lifts, CTR improvements. Strip client names, use category descriptors ("a DTC pet food brand", "a wellness supplement company doing ~$3M/year").
     - **Frameworks and methodologies** — any structured approach Edwin or the team described (rapid testing, sandbox campaigns, insight writing hierarchy, etc.). These become "How We Do It" sections.
     - **War stories** — specific problems the team solved, mistakes they learned from, counterintuitive findings. These are authenticity gold. Anonymize the client but keep the specifics ("We inherited an account where the previous agency had 47 ad sets running with no exclusions between them").
     - **Quotes from Edwin** — things he said in meetings that capture his voice and can be used as pull quotes or section openers. Keep them raw and natural.
     - **Tool and platform insights** — specific findings about Meta, Google, Klaviyo, etc. that demonstrate hands-on expertise ("Meta's default 7-day click / 1-day view window was inflating ROAS by 40% for this account").
   - **Confidentiality rules (hard rules, no exceptions):**
     - NEVER use client names — always anonymize to category + size descriptors
     - NEVER include specific revenue, budget, or total spend amounts
     - Percentage changes and directional metrics ARE okay (CPA dropped 45%, ROAS went from 1.8x to 4.2x)
     - Team member names are okay in internal culture content, but not in public-facing articles attributing client work
     - Candidate names from interviews are NEVER used
     - If a data point is so specific it could identify the client (e.g., "the only DTC hot sauce brand that switched from Shopify Plus to BigCommerce in Q3"), generalize further or skip it
   - If no relevant transcripts exist, note this gap and proceed — the article can still be strong with external research and Jetfuel's general methodology.

5. **Research the competitive landscape and find citeable stats:**
   - WebSearch for the top 5 ranking articles on the target keyword. Note what they cover, how they're structured, and what's missing.
   - WebSearch for LLM-style prompts related to the topic (e.g., "What is [topic]?", "How do I [topic]?", "Best [topic] for [audience]"). Note which brands/sites get cited.
   - **Find authoritative external stats to cite in the article.** For every article, aim for 3-5 third-party data points that add credibility. Search for:
     - Industry benchmarks and reports (e.g., "Meta ads average ROAS by industry 2026", "ecommerce conversion rate benchmarks")
     - Platform-published data (Meta Business Help Center, Google Ads documentation, Klaviyo benchmark reports)
     - Research from Semrush, HubSpot, Statista, eMarketer, Shopify reports, NRF data
     - Analyst reports and surveys (Gartner, Forrester, McKinsey digital reports)
   - **For each stat, capture:**
     - The exact number/finding
     - The source name and publication year
     - A direct URL to the source (verify it loads — do not cite dead links)
   - **Stat quality hierarchy** (prefer in this order):
     1. Platform-official data (Meta, Google, Shopify published stats)
     2. Major research firms (Semrush, eMarketer, Statista, Gartner)
     3. Reputable industry publications (Search Engine Journal, Marketing Dive, Digiday)
     4. Well-known SaaS company reports (HubSpot, Klaviyo, Triple Whale)
     5. Aggregated survey data (never cite a single Reddit comment as a stat)
   - **Never fabricate or hallucinate a stat.** If you can't find a source URL that loads, don't include it. "We've seen across our portfolio" with real anonymized Jetfuel data is better than a made-up industry benchmark.
   - WebFetch at least 2 of the top-ranking competitor articles to understand their depth, structure, and what data they cite. The Jetfuel article should match or exceed their specificity.

### Phase 1: Outline

5. **Build the content outline** using this architecture (adapt section names to the topic, but follow this flow):

   **For blog posts and explainers:**
   ```
   H1: [Question-format title — "What Is X?" or "How to X" or "X vs Y"]

   Opening paragraph: Direct answer in 2-3 sentences. This is the AIO extraction target.
                       Must be quotable, definitional, and self-contained.

   H2: [Core concept / "What is X?" if H1 is broader]
   H2: [Key components / "How it works"]
   H2: [Comparison — "X vs Y" table if applicable]
   H2: [Benefits / "Why it matters"]
   H2: [Use cases / "Who it's for"]
   H2: [Implementation / "How to do it"]
   H2: [FAQ — "Frequently Asked Questions About X"]
       H3: [Question 1 — natural language, how a person would ask it]
       H3: [Question 2]
       H3: [Question 3]
   H2: [Conclusion — 1 paragraph, forward-looking]

   CTA: Single call-to-action tied to the relevant Jetfuel service.
   ```

   **For service pages:**
   ```
   H1: [Service name + audience — "X for Y Brands"]

   Opening: 2-3 sentences positioning Jetfuel for this niche. Include a proof point.

   H2: [The problem this service solves]
   H2: [How Jetfuel approaches it — methodology/process]
   H2: [Results — anonymized case study or data points]
   H2: [What's included / scope of service]
   H2: [FAQ]
       H3: [Question 1]
       H3: [Question 2]
       H3: [Question 3]

   CTA: Contact/consultation CTA.
   ```

6. **Present the outline** to the user for approval before writing. Include:
   - The proposed H1 (exact title)
   - Target word count (1,200-2,000 for blogs/explainers, 800-1,200 for service pages)
   - The 3 FAQ questions
   - Which LLM prompts this content is designed to answer (from the SEO research)
   - Which competitors currently own this space
   - **Transcript insights found** — summarize the usable anonymized data points, war stories, and frameworks pulled from meeting transcripts. If none were found, note that.
   - **External stats sourced** — list the 3-5 third-party data points with sources that will be cited in the article

### Phase 2: Write

7. **Write the full article** following these rules:

   **SEO optimization:**
   - H1 uses the target keyword in question format
   - Target keyword appears naturally in the first 100 words, at least one H2, and the meta description
   - Internal links to existing jetfuel.agency content where relevant (check the site first)
   - URL slug: short, keyword-rich, lowercase, hyphens (e.g., `/meta-health-ad-restrictions-guide/`)
   - Suggest a meta description (under 160 chars, includes keyword, written as a value proposition not a summary)

   **AIO optimization (this is critical):**
   - **Opening paragraph is the extraction target.** Write it as a self-contained, quotable definition or answer. If an LLM reads only this paragraph, it should be able to cite Jetfuel accurately. No throat-clearing, no "In today's rapidly evolving landscape..." — start with the answer.
   - **Every H2 section should be independently extractable.** Each section should make sense if pulled out of context by an LLM.
   - **Use the bold-term-plus-explanation pattern** in all lists:
     - **Term:** One-sentence explanation.
   - **Comparison tables** for any X vs Y content. HTML tables with clear headers. LLMs extract these reliably.
   - **FAQ uses H3 question headings** with concise paragraph answers (2-4 sentences each). These are direct LLM citation targets.
   - **Include structured data recommendations:** Suggest Article schema with full `articleBody`, BreadcrumbList, and FAQPage schema.

   **Edwin's voice (non-negotiable):**
   - Write like you're explaining to a smart friend, not presenting to a boardroom
   - Lead with the insight, not the context
   - Use real numbers and specific examples — "CPA dropped from $292 to $161" not "we significantly reduced costs"
   - Frame challenges as opportunities
   - Keep paragraphs short — 2-3 sentences max
   - Use "we" when talking about Jetfuel's work, not "I"
   - Include actionable takeaways, not vague advice
   - **No corporate jargon used generically** — "leverage", "synergize", "optimize" without specifics
   - **No over-hedging** — "I think maybe we could possibly..." Just say it.
   - **No flowery intros** — get to the point in sentence one
   - **No preachy tone** — earn authority through specifics, not lectures
   - **A little rawness is authentic** — don't over-polish into generic content-mill output
   - **No emojis** unless the user specifically requests them
   - Ground abstract ideas with practical analogies (Edwin's signature move)
   - When referencing Jetfuel results, anonymize clients to category descriptors ("a pet food brand", "a wellness DTC brand")

   **Weaving in transcript insights (what separates this from generic content):**
   - **Every article should include at least 1-2 anonymized real-world examples** from Jetfuel's meeting transcripts. These are the proof points that no competitor can replicate. A specific war story ("We inherited an account running 47 ad sets with zero exclusions — CPA was $292. After restructuring to 8 ad sets with proper exclusions, CPA dropped to $161 in three weeks.") is worth more than any industry benchmark.
   - **Use Edwin's frameworks as section anchors.** If Edwin introduced a methodology in a huddle (rapid testing, sandbox campaigns, insight writing hierarchy), build a section around it. Name it. Make it citeable. ("We call this the Sandbox Method — a dedicated small-budget test campaign in every Meta account, even the small ones.")
   - **Paraphrase Edwin's meeting quotes for pull quotes or section openers.** Don't use them verbatim (they're too conversational for blog format), but preserve the energy: Meeting quote: "It's like a self-driving car — you throw a boulder at it and it swerves and gets confused." Blog version: "Broad-match PMAX is like a self-driving car. Throw one obstacle at it and the algorithm panics — it needs clean lanes to perform."
   - **Place real examples before external stats, not after.** The pattern should be: "Here's what we saw → here's what the industry data says → here's what to do about it." Jetfuel's experience leads, industry data validates.

   **Citing external stats (builds credibility and LLM citability):**
   - **Aim for 3-5 third-party data points per article.** These serve two purposes: they make the content more authoritative for readers, and they create the kind of referenced, data-rich content that LLMs prefer to cite.
   - **Inline citation format:** "According to [Source Name], [stat] ([link])." Or weave naturally: "Meta's own data shows that [stat] — which tracks with what we've seen across our accounts."
   - **Always link to the source.** Use the actual URL, not a vague "according to research." If you can't find a live URL, don't cite the stat.
   - **Combine Jetfuel data + external data for maximum impact:** "We saw ROAS drop 35% across our F&B accounts after Meta's Q4 algorithm update — consistent with the 28% average decline Varos reported across 5,000 DTC accounts ([link])." This pattern is extremely powerful: it says "we're not just reading reports, we're seeing this in our own accounts, and the data backs us up."
   - **Prefer recent data (last 12 months).** A 2024 stat is weaker than a 2026 stat. If only older data exists, note the year.
   - **Platform-official data > everything else.** "Meta's Business Help Center states..." carries more weight than "a marketing blog reported..."

   **Anti-patterns to avoid (from the tone guide):**
   - The formulaic hook-list-lesson-CTA structure
   - "Here's the thing:" / "Here's what I've learned:" / "Let that sink in."
   - Imperative closers directed at the reader — share what WE did, let the reader draw conclusions
   - Symmetric lists (3 bullets that are perfectly parallel in structure)
   - Generic advice dressed as expertise — stay specific to Jetfuel's actual experience
   - **No emdashes (—).** Use commas, colons, parentheses, or separate sentences instead. Emdashes are an AI writing tell.

### Phase 3: Quality Check

8. **Run the content through these checks before presenting:**

   **SEO checks:**
   - [ ] H1 is a question or includes the target keyword
   - [ ] Target keyword in first 100 words
   - [ ] Target keyword in at least one H2
   - [ ] Meta description under 160 chars with keyword
   - [ ] At least one internal link opportunity identified
   - [ ] URL slug is clean and keyword-rich

   **AIO checks:**
   - [ ] Opening paragraph is a self-contained, quotable answer
   - [ ] Comparison table present (if X vs Y content)
   - [ ] FAQ section with H3 question headings and concise answers
   - [ ] Lists use bold-term-plus-explanation format
   - [ ] Each H2 section is independently extractable by an LLM
   - [ ] Schema markup recommendations included (Article + articleBody, FAQPage)

   **Evidence checks (transcript + stats):**
   - [ ] At least 1-2 anonymized real-world examples from Jetfuel transcripts included (if transcripts were found)
   - [ ] No client names, revenue figures, or identifying details leaked
   - [ ] At least 3 third-party stats cited with live source URLs
   - [ ] Every cited stat has a verifiable source — no fabricated data
   - [ ] Jetfuel experience leads, external data validates (not the reverse)
   - [ ] External stat URLs are real and loadable (spot-check at least one)

   **Voice checks (adapted from Edwin's LinkedIn self-check):**
   - [ ] No clean hook-body-lesson-CTA skeleton
   - [ ] At least one moment grounded in Jetfuel's specific experience (anonymized)
   - [ ] No imperative closer or lecture tone
   - [ ] Sounds like someone who does this work, not someone who writes about it
   - [ ] Varied rhythm — mix of short and longer paragraphs
   - [ ] No AI tells ("Here's the thing", "That's it.", "Let me explain.", "The truth is", "Here's why this matters", "In today's rapidly evolving...")
   - [ ] No emdashes (—) anywhere in the article
   - [ ] Paragraphs are 2-3 sentences max
   - [ ] Real numbers or specific examples included (not just generic claims)

   If any check fails, fix it before presenting.

### Phase 4: Output

9. **Present the final content** with:
   - The full article in Markdown
   - Suggested meta description
   - Suggested URL slug
   - Schema markup recommendations (Article with articleBody, FAQPage for the FAQ section, BreadcrumbList)
   - List of LLM prompts this content should now answer
   - List of internal link opportunities on jetfuel.agency
   - **Sources cited** — table of all third-party stats used, with source name, stat, and URL
   - **Transcript insights used** — list of which meeting transcripts contributed data (by topic/date, not client name)
   - Word count

10. **If `--draft` flag was used**, save to Google Docs:
   - Create a new Google Doc using `create_doc`
   - Title: the H1
   - Write the full content using `batch_update_doc`
   - Share the Doc link with the user

## Important Rules

- **The opening paragraph is the most important paragraph.** It's what LLMs will extract and cite. Spend disproportionate effort on making it quotable, accurate, and self-contained. If it starts with "In today's..." or any throat-clearing, delete it and start with the actual answer.
- **Tables are LLM magnets.** Any time you're comparing two things, use a table. LLMs reliably extract HTML/Markdown tables for comparison queries.
- **FAQ questions should be written as real people would ask them** — conversational, not keyword-stuffed. "What's the difference between X and Y?" not "X vs Y comparison overview."
- **Never fabricate case study data. This is a hard rule, no exceptions.** Do not invent metrics, ROAS figures, CPA numbers, spend levels, or percentage changes, even if anonymized. If real data exists in transcripts, use it. If it doesn't, insert a `[NEEDS REAL DATA]` placeholder with instructions for the team to fill in verified numbers from actual accounts. "We've seen strong results across our F&B portfolio" with a placeholder is always better than a made-up "1.8x to 4.2x ROAS" that sounds plausible but isn't real. When using data from transcripts, also add `[VERIFY]` tags for any specific numbers so the account lead can confirm before publishing.
- **Word count targets are guidelines, not mandates.** 1,500 well-written words beat 3,000 padded words. If the topic is covered in 1,200 words, stop there.
- **The article should answer at least 2-3 LLM prompts** from the research. If it doesn't, the content strategy is off — revisit the outline.
- **Schema markup is not optional.** Every piece of content should include `articleBody` in Article schema (this is what makes JS-rendered content readable by crawlers and LLMs) and FAQPage schema for the FAQ section.
- **One CTA maximum.** Place it after the conclusion. Don't interrupt the content with CTAs — it hurts dwell time and breaks the reader's trust.
- **Anonymize all client references.** Use category descriptors ("a DTC food brand doing $3M/year") never client names.
