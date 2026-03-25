---
name: llm-prompt-research
description: Research and validate the top LLM prompts a brand should target for AI visibility — grounded in real data, not SEO keywords
---

# LLM Prompt Research

Given a brand/domain, research how it shows up (or doesn't) in LLM-generated answers, then produce a validated list of the top 10 prompts the brand should target for AI visibility.

## Arguments

The user may specify:
- A domain (e.g., `thinkjinx.com`, `barkerwellness.com`). Required.
- A target query/topic (e.g., "dry dog food for puppies", "CBD for dogs"). Optional — if omitted, infer from the site.
- `--competitors` to include competitor comparison. Default: yes.

## Key Principle: Prompts, Not Keywords

People don't type SEO keywords into LLMs. They describe problems, constraints, and situations conversationally. The output of this skill is **real prompts people would type into ChatGPT, Claude, Perplexity, or Gemini** — not Google search keywords.

The three prompt archetypes that drive brand recommendations:
1. **Problem/Symptom** — "My [situation/problem], what should I [do]?"
2. **Buyer-Intent Shopping** — "I'm looking for [product] that [constraint]. What are good options?"
3. **Comparison/Validation** — "Is [brand] good?" / "How does [brand] compare to [competitor]?"

## Steps

### Phase 0: Internal Context — Meeting Transcripts

0. **Read client meeting transcripts** from Google Drive before doing any external research:
   - Identify the client name from the domain (e.g., `thinkjinx.com` → "Jinx")
   - Search Google Drive for meeting transcripts: use `mcp__google-workspace__search_drive_files` with the client name
   - Read the transcripts using `mcp__google-workspace__get_doc_as_markdown`
   - Extract and note:
     - **Brand voice and positioning** — how the client talks about themselves
     - **Target audience** — who they're trying to reach
     - **Competitive landscape** — who they see as competitors (may differ from what LLMs think)
     - **Current marketing strategy** — what channels, what's working, what's not
     - **Pain points and goals** — what they've told us they want to improve
     - **Specific products/claims they emphasize** — these should weight the prompt list
     - **Any existing SEO/content strategy** — so we don't duplicate or contradict
   - If a client brief already exists at `.claude/ops/ad-copy-analyzer/client-briefs/{client}.md`, read that too — it may contain relevant context from prior analysis
   - This internal context is critical: it tells you what the client CARES about winning on, not just what they sell. A prompt the client has explicitly said they want to own should rank higher than one we inferred from their site.

### Phase 1: Brand Reconnaissance

1. **Fetch the brand's website** using WebFetch:
   - Homepage: product categories, positioning, unique claims, target audience
   - Product pages: specific SKUs, life stages, use cases, key differentiators
   - Blog/content: what queries their existing content answers
   - Note what's MISSING — content gaps are opportunities

2. **Check third-party reviews** via WebSearch:
   - Dog Food Advisor (or category equivalent), Chewy, Amazon ratings
   - Review sites: Dogster, Honest Brand Reviews, Consumer Rating, etc.
   - Note: star ratings, review counts, recall history

3. **Identify the competitive set** — who are the brands LLMs currently recommend for this category? Search for the obvious category queries and note every brand mentioned.

### Phase 2: Current AI Visibility Baseline

4. **Check Semrush Free AI Visibility Checker:**
   - Note: the free tool requires browser interaction and may not be scrapable
   - If unavailable, document as "needs manual check" and provide the URL
   - URL: `https://www.semrush.com/free-tools/ai-search-visibility-checker/`

5. **Search for existing AI visibility studies** in the brand's category:
   - WebSearch for: `AI visibility [category] brands index 2026`
   - WebSearch for: `[brand name] AI visibility ChatGPT recommendations`
   - Look for Brandi AI indexes, Semrush reports, GEO case studies
   - Extract: which brands dominate, which sources LLMs cite, which prompts were tested

6. **Test live LLM retrieval** — run the obvious category queries through WebSearch (which simulates what LLMs with RAG would retrieve):
   - The brand's core category query (e.g., "best [product category]")
   - A problem-based query (e.g., "my [user] has [problem], what helps?")
   - A branded query (e.g., "is [brand] good?")
   - A comparison query (e.g., "[brand] vs [top competitor]")
   - For each: does the brand appear in the top 10 results? Which competitors dominate?

### Phase 3: Validate Against Real User Behavior

7. **Check public conversation datasets** for real prompt patterns in this category:
   - Search HuggingFace datasets API:
     - `https://datasets-server.huggingface.co/search?dataset=allenai/WildChat-1M&config=default&split=train&query=[category keywords]&offset=0&length=20`
     - Also try `allenai/WildChat-4.8M` and `lmsys/lmsys-chat-1m` (note: LMSYS is gated)
   - Extract EXACT user prompts — do not paraphrase
   - Key finding to look for: do people ask for brand recommendations, or do they describe problems/symptoms and expect the LLM to recommend solutions?

8. **Check ChatGPT Shopping data** (if product/ecommerce brand):
   - WebSearch for category-specific ChatGPT Shopping patterns
   - Note: ChatGPT Shopping pulls 83% of product carousels from Google Shopping
   - Retailer-constrained queries ("best [product] at [retailer]") are a growing pattern

9. **Cross-reference with industry sources:**
   - Search for: `[category] most common questions people ask`
   - Check Reddit for real discussions: `reddit [category] recommendation chatgpt AI`
   - Check if the brand's category has published AI visibility research (Brandi AI, Semrush, etc.)

### Phase 4: Score and Rank

10. **Build the prompt list** — for each candidate prompt, evaluate:

    | Factor | Weight | Description |
    |--------|--------|-------------|
    | **Validated** | 30% | Is there evidence real people ask this? (dataset match, search volume, industry study) |
    | **Brand fit** | 25% | Does the brand have a specific product/claim that answers this prompt? |
    | **Winnable** | 25% | Can the brand realistically appear in LLM answers? (existing citations, content gap size) |
    | **Volume** | 20% | How frequently would this prompt be asked? (use search volume as proxy) |

    Classify each prompt's evidence level:
    - **Confirmed** — found in public dataset or industry study
    - **Strong signal** — matches known user behavior patterns from research
    - **Inferred** — logical extrapolation from brand strengths, not directly validated

### Phase 5: Output

11. **Format the Slack message** using this structure. Use proper case (not all lowercase). Keep it concise but include enough context that each section is actionable and educational for the team.

    ```
    *[Brand Name] — AI Visibility Analysis*

    [1-2 sentence summary of the situation. What did the research find? Include the AI Vol score.]

    [1 sentence on who LLMs currently recommend instead. Name the specific competitors.]

    _Quick context for the team: [1-2 sentences explaining WHY this matters — how LLM visibility
    works differently from SEO. Keep it brief but educational. The team should learn something
    from every report.]_

    ---

    *Top 10 Prompts [Brand] Should Be Showing Up For*

    *Problem/pain — how people actually start these conversations:*

    > 1. [conversational prompt]
    > 2. [conversational prompt]
    > 3. [conversational prompt]

    *Shopping — people actively looking to buy:*

    > 4. [conversational prompt]
    > 5. [conversational prompt]
    > 6. [conversational prompt]

    *Validation — people comparing or vetting the brand:*

    > 7. [conversational prompt]
    > 8. [conversational prompt]
    > 9. [conversational prompt]

    *Authority — own the category knowledge:*

    > 10. [conversational prompt]

    ---

    *Why [Brand] Isn't Showing Up*

    [2-3 bullet points explaining the specific gaps. Be concrete — name the missing
    listicles, the content that doesn't exist, the editorial coverage that's absent.
    End with the key insight from the meeting transcripts if applicable.]

    ---

    *Next Steps*

    *1. [Action title]*
    _Owner: [team/role] | Deadline: [specific timeframe]_
    [2-3 sentences explaining what to do. Be specific enough to drop into a ClickUp task.
    Include target URLs, target contacts, or exact deliverable specs.]
    • [bullet details as needed]

    *2. [Action title]*
    _Owner: [team/role] | Deadline: [specific timeframe]_
    [Same format. Every action needs an owner and a deadline.]

    [Continue for 3-5 next steps total. Each should be independently assignable.]
    ```

    **Formatting rules:**
    - Use proper case throughout (capitalize normally). Not all lowercase.
    - Prompts inside blockquotes should be written naturally — how a real person would type them into ChatGPT. Proper case is fine for prompts too.
    - Bold for section headers, italic for owner/deadline lines.
    - Bullet points (•) for supporting details under each action.
    - Keep the total message scannable — a manager should be able to read it in 2 minutes and assign tasks from it.
    - Include one educational line (italic, 1-2 sentences) near the top so the team builds understanding of LLM visibility over time. Don't over-explain — just enough that someone new to this concept gets the gist.

12. **Post to the appropriate Slack channel** using the Slack API (chat.postMessage via curl). Before sending:
    - Run proofread assertions (no standalone "0k", no "$0", no placeholder text)
    - Verify key brand names, stats, and dollar figures read correctly
    - Re-read the full message once before posting

## Important Rules

- **Proofread every prompt and every line of output before posting.** Re-read the full Slack message word by word before sending. Look for:
  - Nonsensical phrases (e.g., "under $0", "agency under $0", "wine under $0")
  - Placeholder text or template fragments that weren't filled in
  - Dollar amounts, percentages, or stats that don't make sense in context
  - Brand names or product names that are misspelled or don't exist
  - Claims that contradict what the research actually found
  - Sentences that trail off or repeat themselves
  If anything looks off, fix it before posting. Do not send a message you haven't fully re-read.

- **Never output SEO keywords as prompts.** The output must be conversational, natural-language prompts that a real person would type into ChatGPT or Claude. If a prompt reads like a Google search ("best dry dog food 2026"), rewrite it as a conversation ("What should I feed my new puppy?").

- **Always show your evidence.** For each prompt, cite whether it was validated by a dataset, an industry study, search result patterns, or inferred from brand analysis. Be honest about what's confirmed vs. assumed.

- **Problem-first, not product-first.** The highest-value prompts are where people describe a problem and expect the LLM to recommend a solution. These are harder to win but more valuable than branded queries.

- **Check for existing AI visibility research** in the category before doing primary research. Someone may have already done this work (Brandi AI, Semrush, GEO case studies).

- **The WildChat insight matters.** In public datasets, people rarely ask LLMs for direct brand recommendations. They ask about problems, symptoms, and how-tos. The brand recommendation happens as part of the LLM's answer to their real question. Build the prompt list around this reality.

## Reference: Data Sources

| Source | What it provides | Access |
|--------|-----------------|--------|
| [Semrush AI Visibility Checker](https://www.semrush.com/free-tools/ai-search-visibility-checker/) | Brand mentions across ChatGPT, Gemini, AI Overviews | Free (1/day), $99/mo full |
| [WildChat-4.8M](https://huggingface.co/datasets/allenai/WildChat-4.8M) | 4.8M real ChatGPT conversations | Free, HuggingFace |
| [LMSYS-Chat-1M](https://huggingface.co/datasets/lmsys/lmsys-chat-1m) | 1M real multi-LLM conversations | Free, gated (needs license agreement) |
| [Brandi AI Indexes](https://mybrandi.ai/) | Category-specific AI visibility rankings | Reports published per category |
| [Semrush Prompt Database](https://www.semrush.com/kb/1503-prompt-tracking) | 239M real ChatGPT/Gemini prompts | $99/mo |
| ChatGPT Shopping | 50M daily shopping queries, 83% from Google Shopping | No direct access — research via Semrush blog |
| [Adobe LLM Optimizer](https://business.adobe.com/products/llm-optimizer.html) | Enterprise brand citation tracking | Enterprise pricing |

## Reference: Key Research Findings

These findings should inform how you weight and frame prompts:

- **70% of ChatGPT queries don't match traditional search patterns** (Semrush)
- **54% of users ask LLMs to compare products directly** (Semrush)
- **AI search visitors convert 4.4x better** than traditional organic search visitors
- **ChatGPT Shopping pulls 83% of carousel products from Google Shopping** (Semrush)
- **50M daily shopping queries** processed by ChatGPT (Dataslayer)
- **LLMs draw from a narrow, recurring set of trusted sources** — Business Insider, PetMD, DFA, AKC, Reddit, YouTube (Brandi AI)
- **In WildChat (4.8M conversations), direct brand recommendation requests are rare** — people ask about problems/symptoms, LLMs recommend brands as part of the solution
