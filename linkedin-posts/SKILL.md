---
name: linkedin-posts
description: Generate LinkedIn thought leadership posts from this week's meeting transcripts
disable-model-invocation: true
---

# LinkedIn Posts

Generate LinkedIn thought leadership posts from the week's Google Meet transcripts, written in the user's authentic voice.

## Steps

1. **Load identity and settings:**
   - Read `.claude/me.md` for user identity. If missing, STOP and tell user to run `./setup.sh`.
   - Read `.claude/me.json` for user preferences.
   - Read `.claude/edwin-tone-guide.md` for voice and style rules — especially the **LinkedIn Post Writing Guide** section. This is the single most important file for this skill.

2. **Find this week's transcripts:**
   - Run `date` to get today's date, then calculate the most recent Monday (start of week).
   - Search Google Drive for transcripts modified since that Monday:
     - `fullText contains 'transcript' and modifiedTime > '{monday_date}'`
     - `name contains 'meeting' and modifiedTime > '{monday_date}'`
     - `name contains 'Notes by Gemini' and modifiedTime > '{monday_date}'`
   - Deduplicate results by document ID.
   - Exclude any transcripts that Gemini couldn't process (empty summary/details).

3. **Read all transcripts:**
   - Use `get_doc_as_markdown` to read each transcript in full (include_comments: false).
   - Fetch in parallel batches of 5 to stay within rate limits.

4. **Extract post-worthy insights:**
   - For each transcript, identify the single most LinkedIn-worthy insight. Prioritize:
     - Counterintuitive findings (something that surprised the team)
     - Specific metrics or results (CPA changes, conversion lifts, engagement data)
     - Strategic decisions with clear reasoning
     - Hiring/team/culture moments that reveal how the agency operates
     - Process innovations or framework introductions
   - Skip transcripts that are purely operational (status updates with no insight) or confidential (sensitive compensation, HR issues, or client financials that shouldn't be public).
   - **Confidentiality rules:**
     - NEVER name specific clients in posts. Use category descriptors ("a pet food brand", "a wellness DTC brand", "a client in the mattress space").
     - NEVER include specific revenue numbers, budgets, or spend amounts that could identify a client.
     - CPA, ROAS, CTR, and conversion rate CHANGES (percentages, directional) are OK.
     - Team member names are OK for internal culture posts, but ask first if unsure.
     - Candidate names from interviews should NEVER be used.

5. **Write posts following the tone guide:**
   - Apply every rule from the **LinkedIn Post Writing Guide** in `edwin-tone-guide.md`.
   - Each post must pass the **Self-Check** checklist before being included.
   - Target length: 150-300 words per post. No shorter than 120, no longer than 350.

6. **Self-check all posts:**
   Run every post through the self-check from the tone guide:
   - [ ] No clean hook-body-lesson-CTA skeleton
   - [ ] At least one moment that could ONLY come from the user's specific experience
   - [ ] No imperative closer or lecture
   - [ ] Sounds like someone talking, not writing an essay
   - [ ] Varied rhythm — mix of short and longer paragraphs
   - [ ] No symmetric lists
   - [ ] No AI tells ("Here's the thing", "That's it.", "Let me explain.", "The truth is", "Here's why this matters")

   If a post fails any check, rewrite it before presenting.

7. **Present results:**
   - Show each post with a label indicating which meeting it came from (use category, not client name).
   - Include the self-check pass/fail status.
   - Ask user if they want to save to a Google Doc for editing and scheduling.

8. **Update state:**
   - Write `.claude/ops/linkedin-posts/state.json` with:
     ```json
     {
       "last_run_at": "{ISO_timestamp}",
       "week_of": "{monday_date}",
       "transcripts_processed": 0,
       "posts_generated": 0,
       "transcript_ids": []
     }
     ```

## Notes
- Never use client names — always anonymize to category descriptors
- Never include exact revenue, budget, or spend figures
- Never name interview candidates
- When in doubt about confidentiality, skip the transcript
- The tone guide is the source of truth — if a post sounds like AI, kill it and rewrite
- One post per transcript maximum. Quality over quantity.
- If fewer than 3 transcripts have post-worthy insights, that's fine. Don't force weak posts.
