---
name: humanize-writing
description: Write or rewrite text so it reads like a person wrote it, not an AI. Uses the full catalog of AI tells from Wikipedia's "Signs of AI writing" plus the 2025-2026 lists (Forbes, tropes.fyi, and others). Use this whenever you draft or edit prose meant for other people: emails, cover letters, hiring or outreach messages, LinkedIn posts, resume bullets, bios, blog posts, docs, READMEs, PR descriptions, or Slack messages. Also use it when the user says "humanize", "make this sound human", "doesn't sound like AI", "less robotic", "less ChatGPT", "sounds too AI", "pass AI detectors" or "ZeroGPT", or pastes text and asks you to clean it up or make it more natural. Use it even when the user doesn't mention AI at all but asks for any polished writing they'll send or publish.
---

# Humanize writing

Readers and detectors (ZeroGPT, GPTZero, Turnitin, and Wikipedia editors) spot AI text from a small set of habits that repeat: certain words, certain sentence shapes, even rhythm, and chatbot leftovers. This skill exists so those habits never reach anything the user sends. One tell on its own proves little. Text gets flagged when several pile up, so the aim is none.

The full catalog, with every banned word and template, is in `references/ai-tells.md`. Read it before your first draft in a session, and again whenever you're unsure whether a phrase is a tell.

## Workflow

1. **Understand the destination.** Who reads it, and where (email, LinkedIn, resume, doc)? Plain-text destinations get no Markdown at all. Check for user or project rules that override defaults (house style, required keywords, banned characters).
2. **Draft plainly.** Write the way the user would explain it to a peer. Start with the point. Use concrete facts they gave you: numbers, names, tools, dates. Never invent facts to make the writing livelier. A plain true sentence beats a vivid made-up one.
3. **Scan against the catalog.** Go section by section through `references/ai-tells.md`: vocabulary, templates, structure, formatting, chatbot artifacts. Fix each hit by rewriting the sentence, not by swapping in a synonym. Synonym swaps usually leave the same template in place.
4. **Score it** when the text is more than a couple of sentences:
   ```
   python3 <skill-dir>/scripts/ai_detect.py <file> --md
   ```
   Save the draft to a temp file first. The scorer is a local, offline approximation of ZeroGPT/GPTZero (0-100, higher = more AI-like). It lists flagged sentences with reasons. Rewrite the flagged ones worst-first and re-score. Keep a rewrite only if the score drops. Targets: 30 or below for messages and prose; 40 or below for resumes and bullet lists, since list structure keeps some signal.
5. **Deliver** the final text. If you're rewriting the user's own text, briefly note the main kinds of changes (for example "dropped the 'not X but Y' openers, split two long sentences") so they learn the patterns. Don't pad the delivery with praise or a summary moral.

## The rules that matter most

These cause most flags. The reference file has the complete list.

- **No negative parallelism.** "It's not X, it's Y", "This isn't about X. It's about Y", "Not only... but also". It's the most-cited tell of all. Just say what the thing is.
- **No rule of three by reflex.** "fast, reliable, and scalable". Use two items, or four, or one. One three-item list per paragraph at most.
- **No "-ing" tails that fake analysis.** ", highlighting the importance of...", ", ensuring...", ", paving the way for...". Give the concrete effect its own sentence with a subject, or cut it.
- **No AI vocabulary.** delve, tapestry, testament, pivotal, crucial, underscore, showcase, foster, leverage, seamless, robust, landscape, journey, meticulous, vibrant. Also the 2026 fillers: quietly, shift, matters, "the real problem", "the work", load-bearing.
- **Write "is" and "has"** in place of "serves as", "stands as", "boasts".
- **No ta-da lines.** "Here's the thing", "The result?", "Let that sink in", or a rhetorical question answered in the next line.
- **Vary sentence length.** Even rhythm is what detectors measure first. Put a 5-word sentence next to a 25-word one. Vary paragraph length too.
- **No summary closers or morals.** "In summary", "Overall", "Ultimately", or an upbeat final line. Stop when you're done.
- **No em dashes (—).** Use a comma, full stop, colon, or parentheses. En dashes in date ranges are fine.
- **No chatbot leftovers.** "I hope this helps", "Certainly!", "Great question", "Let me know if...", "As of my knowledge cutoff", placeholders like [Your Name].
- **No elegant variation.** Once something has a name, keep using it. Don't rotate synonyms to avoid repeating a word.

## Voice to aim for

- Plain verbs: built, ran, fixed, wrote, moved, shipped, cut, led, found.
- Contractions in messages and emails (I'm, it's, didn't).
- Don't start consecutive sentences with the same word, especially "I".
- A short fragment now and then is fine. So is starting a sentence with "And" or "But".
- For a gap or limitation, one honest plain line beats a polished pivot.

## Exceptions

- **Resumes and ATS keywords.** If a job description uses a banned word as a skill or keyword (say "scalable" or "end-to-end"), the resume may use it once where keyword matching needs it. Never in outreach messages.
- **Project conventions win on formatting.** For example, a LaTeX resume that bolds metrics with `\textbf{}` keeps that convention.
- **Quoting the user or a source.** Keep quotations as written. These rules apply to your own words.
