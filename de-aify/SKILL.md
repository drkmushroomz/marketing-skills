---
name: de-aify
description: Use when writing or revising any client-facing or public copy (proposals, JDs, emails, Slack digests, ad copy, blog posts, deck or slide copy) that reads like AI, or when someone says "de-aify this", "make it sound human", "this reads like ChatGPT/AI", "strip the AI tells", or flags AI voice, cadence, or slop in a draft. Also use as the final pass before shipping any written deliverable.
metadata:
  version: 1.0.0
---

# De-Aify

## Overview

A portable checklist for making written work stop reading like AI. Word-level scrub first, cadence read second, specifics throughout. Works on JDs, proposals, emails, Slack digests, ad copy, blog posts, deck copy, anything.

This is the de-aify mechanics only. It is not a full voice or brand guide, so it works on any copy in any voice. It tells you how to strip the AI fingerprint without telling you what to sound like.

**Core principle: two passes, in order, across every surface.** Word-level scrub, then a separate read-out-loud cadence pass, both run over ALL the text (headings, `<summary>` and accordion labels, table captions, buttons, tooltips, alt text, footnotes, metadata), not just the body paragraphs. The scrub is a find-and-replace job. The cadence read catches what a checklist cannot: the self-sealing closer, the "X, not Y" bow, the compound "X, and Y" title tail, the rule-of-three. A line can pass every word-level filter and still read like a machine because of its rhythm, and headings and labels carry those tells more than paragraphs do. Skipping the second pass, or running it on prose only, is why "de-aified" copy still reads like a robot. Run all parts and clear the ship gate before you ship.

## When to use

- Final pass before shipping any client-facing or public deliverable.
- Anytime a draft (yours or an AI's) needs the AI fingerprint removed.
- When Edwin or a teammate flags AI voice, cadence, filler, or slop in copy.

Not a substitute for a brand or voice guide. This strips tells; it does not decide what you sound like. For Jetfuel proposal/pitch voice specifically, pair with the pitch-sites skill.

## Part 0: De-aify is additive (read this first)

Removing tells is the smaller half of the job. The strongest signal a human wrote something is a concrete, checkable specific that only this person or company could have written. A clean, well-scrubbed line can still read AI if it says nothing you could argue with.

Two versions, both scrubbed. The second is the one a human wrote:

- Generic: "Clients stay because the strategy is working and the numbers show it."
- Human: "great client NPS scores, 90%+ retention and you hit the forecasts you set."
- Generic: "You spot what's worth testing next and put enough budget behind it to get a real read."
- Human: "cook up the hypothesis and deliver real post-test analyses that drive future tests."

The rules:

1. **Every claim carries a checkable specific.** A number, a named standard, a real behavior, or a relational word. The test: could a reader argue with this specific? If there is nothing to push back on, it is generic filler even when the words are clean.
2. **Specificity outranks cadence.** When you can only fix one thing, add a real detail before you smooth a sentence. A rough, specific line beats a smooth, abstract one every time.
3. **Inject, do not only delete.** At least one per section: an operator verb ("cook up," "get stuff done"), a real metric, a named standard, a relational word.
4. **Polish is a separate pass.** Light mechanical roughness (a dropped period, an ampersand, a fast run-on) reads human. Sanding it into corporate smoothness is itself a tell. Do the de-aify work first, then a distinct polish pass for client- or candidate-facing docs, and surface nits as a list instead of auto-smoothing them.
5. **Flip the self-check.** Do not only ask "does this contain a tell?" Ask "does each claim contain a truth only this company could write?" If a section has zero specifics a competitor could not copy, it is not done.

## Part 1: Word-level scrub

Search and kill these. They read clean in isolation and still flag AI.

**Punctuation**
- No em dashes, ever. Use a period, a comma, or split the sentence. (Hard rule.) No en dashes in prose either.

**Corporate jargon used generically**
- synergize, leverage, optimize, robust, delve, utilize, facilitate, streamline

**Filler intensifiers and hedges**
- "very," "really," "truly," "incredibly," stacked qualifiers ("I think maybe we could possibly")

**Transitional tells (a pivot to a packaged insight)**
- "Here's the thing," "Here's what I've learned," "The truth is," "Let me explain," "That's it.," "Let that sink in.," "Read that again."

**Packaged-insight clichés (hard blocklist)**
- move the needle, north star, secret sauce, game-changer, raise the bar, level up, take it to the next level, at the end of the day, best-in-class, hit the ground running, low-hanging fruit, unlock (as a verb), supercharge, 10x (as a hype adjective), single source of truth (unless it is literally technical)

The fix is not a fresher synonym. Cut the phrase and state the plain fact, ideally with a concrete detail a practitioner would actually say.

## Part 1.5: Both passes cover EVERY text surface, not just paragraphs

The single most common miss is running both passes on the body prose and skipping every other piece of text. Do not. The cadence tells, especially the compound "X, and Y" tail, the "X, not Y" antithesis, and the appositive "X: Y" label, hide in titles and labels MORE than in paragraphs. A heading is short enough to feel finished and long enough to carry a bow, so it slips through when you only read the paragraphs.

Sweep every one of these, in BOTH the word-level scrub and the out-loud cadence read:
- Page and section headings, subheads, kickers, eyebrows, the title tag and subtitle
- Collapsible / accordion / `<summary>` / `<details>` labels, tab labels
- Table captions, column headers, row labels
- Card titles, stat labels, callout titles, badge / pill / tag text
- List items and spec / channel / metric rows
- Button, link, and CTA labels; nav and menu items
- Tooltips, hovers, empty-state text, error text, placeholder text
- Image alt text and captions; chart, axis, and legend titles
- Footnotes, disclaimers, bracketed editor flags (`[assumption]`, `[TBD]`)
- Metadata: page title, slug, meta description, email subject lines, filenames, commit and PR titles

Heading and label tells to kill on sight (this is where they live):
- Compound "X, and Y" title tails: "New versus repeat by channel, and the two ways to read it" becomes "New versus repeat, by channel."
- Antithesis titles: "...that hold up, and that don't"; "(measured, not assumed)"; "views, not clicks" become the one plain thing: "Which keywords hold up"; "(measured)"; "How much runs on ad views."
- Appositive parenthetical bows: "(this is the part that matters)", "(and why it works)" get cut.
- The colon-plus-promise: "The one number that changes everything:" cut the promise, keep the label.

A heading is done when it names its content in the fewest plain words and carries no rhetorical tail. If you can only skim one thing before shipping, skim the headings and labels, because that is where a reader spots the AI first.

## Part 2: Cadence read (out loud)

The word-level scrub does not catch these. They read clean word by word and still scream AI. You only catch them by reading for rhythm. After the scrub, read the whole thing out loud and hunt for these four. Run it across every surface listed in Part 1.5, not just prose paragraphs. The fragments hide in headings, `<summary>` labels, table captions, and bracketed flags.

**1. Aphoristic setup plus self-sealing closer.** A tidy little maxim that wraps itself in a bow. The sentence congratulates itself.
- AI: "You find the next channel before it's obvious, and you run the test that proves it."
- Plain: "You spot what's worth testing next and put enough budget behind it to get a real read."

**2. Antithesis bow ("X, not Y" / "X instead of Y").** A closer that props itself against a strawman to sound decisive: "outcomes, not vanity metrics." One or two in a whole doc is fine. A cluster is a fingerprint, and the "not Y" half is usually deletable. (Additive "not just X but also Y" is fine; it is the punchy "X, not Y" tagline that is banned.)

**3. Rule of three / tricolon.** Three balanced beats: "you find X, put Y behind them, and decide Z." AI reaches for the triad by default. Real speech is lopsided. The balanced two-beat is the same tell in miniature. Cut to fewer beats, or make them uneven in length and shape.

**4. Stacked flourishes.** Consecutive clauses that each end on a rhetorical grace note ("before anyone asks," "at a scale most strategists can't touch"). Swap each grace note for a concrete specific.

**Also watch the terse-fragment punch.** "Reach and video are the job." "Two PMax campaigns are the retail-support engine." "The X is the point." These pass the word-level scrub (no em dash, no buzzword, no "not Y") and are pure copywriter punch. Cut the fragment or state the plain fact ("It books zero purchase conversions by design," "Two PMax campaigns drive store visits").

**The "X, Y, Z" verbless fragment stack.** A "sentence" that is a noun phrase trailed by two or more comma-chained modifiers or appositives with NO main subject-verb: "Top-of-funnel video against oral-care and wellness content, geo-targeted around the retail footprint, ahead of the shelf." Also "SPINS or Circana plus the feed, the numbers a buyer reads at the line review" and "Sensitivity and dry mouth, the pain the buyer feels, ahead of the ingredient name." It reads as an AI list-fragment. It hides most often in card/tile copy, stat captions, and channel descriptions, not body prose. Test: read the line aloud and look for a main verb; if there is none, it is the stack. Fix by giving it a subject and a verb ("We run top-of-funnel video against X and geo-target it around Y"). Applies to card copy, captions, and labels, not just paragraphs (Edwin flagged this on David's v3).

**Compressed zero-relative clause + contraction.** "the doors David's just won," "the stores we'd opened," "the audience Meta's built" drop the relative pronoun and stack it on a contraction, so the reader re-parses who did what. Do NOT fix by inserting "that" ("the doors that David's won" is still clunky). Restructure into a plain noun phrase or a clear subject-verb: "the doors David's just won" becomes "David's new doors"; "the audience Meta's built" becomes "the audience Meta built for us" or just "Meta's audience." Prefer immediately readable subject-verb order over a saved word. Edwin flagged this on David's v3.

**Also watch the colon-list compound (the verbose AI sentence).** One sentence that states a claim, hangs a by-agent modifier on it, then unloads a colon list of two parallel appositive clauses, each carrying its own relative clause: "This layer runs two tracks in parallel, funded by the efficiency the program above buys back: retail support that drives velocity at the doors just won, and awareness that reaches the majority the brand already misses." It passes the word-level scrub and is pure machine cadence, and it almost always hides passive voice ("funded by," "is built for," "measured on"). Fix: break it into two or three short ACTIVE sentences that name the actor, and drop the colon and the "A that Xs, and B that Ys" scaffolding. Before/after that landed: "...funded by the efficiency the program buys back: retail support that drives X, and awareness that reaches Y" became "The efficiency gains above pay for two more tracks. Retail support drives X, and awareness reaches Y." Edwin flagged this exact structure on the David's proposal: "avoid these verbose AI tell sentence structures, i would rather have 2 sentences there, avoid passive voice."

**Watch the fix itself.** The trap is replacing one rhetorical closer with another. "...and you run the test that proves it" got rewritten as "...and decide with the data instead of a hunch," which is the same bow wearing new words. When a line reads AI, make it PLAINER, not cleverer. Cut the closer, do not re-dress it. If a line could drop into any agency's copy unchanged, it is too generic.

## Part 3: Structural tells (long-form and social)

For posts, articles, and anything with more than a few paragraphs.

1. **The formulaic hook, list, lesson, CTA skeleton.** Hook line. Bullet list of three. Insight paragraph. Imperative closer. Break it.
2. **Imperative closers aimed at the reader.** "Simplify your naming convention." "Stop doing X." Share what YOU did and let the reader draw the conclusion.
3. **Over-polished flow.** Every paragraph gliding into the next like a structured essay. Real writing has seams, tangents, and asides.
4. **Generic advice dressed as a story.** A specific anecdote that zooms out into universal wisdom. Stay specific.
5. **Symmetry.** Three bullets, three examples, three takeaways. Real people do not think in symmetric lists. Cut to two or make them uneven.
6. **Even depth.** Spend 60% of the space on the part that actually matters, not equal time on setup, lesson, and closer.
7. **Tidy endings.** Not every piece needs a bow. "We'll see." and "Still early." are fine.

## Ship gate: the self-check

Do not ship until every box is checked.

- [ ] **Word-level scrub done.** Searched for em dashes, jargon, filler, transitional tells, and the cliché blocklist. All gone.
- [ ] **Every surface swept.** Both passes covered headings, subheads, `<summary>` / accordion / tab labels, table captions and column headers, card and stat labels, buttons and CTAs, tooltips, alt text, captions, footnotes, bracketed flags, and metadata (title, subtitle, slug, subject lines). Not just body prose.
- [ ] **Read out loud.** Hunted the four cadence tells. No self-sealing closers, no "X, not Y" clusters, no compound "X, and Y" title tails, no default tricolons, no stacked flourishes, no terse-fragment punch.
- [ ] **The fix stayed plain.** No rhetorical closer got swapped for a fresher one.
- [ ] **Specifics present.** Every section has at least one detail a competitor could not copy. A number, a named standard, a real behavior, or a relational word.
- [ ] **Fingerprint check.** At least one moment that could only come from this specific person or company.
- [ ] **Structure broken (long-form).** No clean hook-list-lesson-CTA skeleton, no reader-directed imperative closer, no forced symmetry.

The non-negotiable: word-level scrub, then a separate out-loud cadence read. Ship only after the second pass.

## Running it as an AI instruction

Pasting this skill above a draft and asking for a de-aify works, but an AI running the checklist will miss its own cadence tells. Always eyeball the result and do the out-loud cadence read yourself. When possible, write to a local file first: shipping straight to a Google Doc or CMS via MCP skips any local AI-tell hook and the cadence read is the only thing that catches the rest.

## Common mistakes

| Mistake | Fix |
|---|---|
| Stopping after the word-level scrub | The scrub catches half. Do the separate out-loud cadence read. |
| Swapping one closer for a fresher one | Make it plainer, not cleverer. Cut the closer, do not re-dress it. |
| Only running the read on prose | Sweep EVERY surface (Part 1.5): headings, `<summary>`/labels, table/column headers, buttons, tooltips, alt text, captions, footnotes, metadata. Titles and labels carry the "X, and Y" / "X, not Y" tells more than paragraphs do. |
| Scrubbing clean but staying generic | De-aify is additive. Add a checkable specific to every claim. |
| Auto-smoothing rough edges | Light roughness reads human. Surface nits as a list; do not sand to corporate smooth. |
