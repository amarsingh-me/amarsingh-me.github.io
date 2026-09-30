---
name: teach-me
description: Run the full learn-a-topic-and-publish-it workflow for this blog/notes repo - suggest or take a tech topic, teach it interactively in conversation, then once the user signals they're ready, write it up as a short blog-format note, place it in the right content/blogs category (creating a new one if none fits), and create a new git branch for it. Use when the user invokes /teach-me, asks to learn a new topic and document it, says "teach me X", or asks to turn a discussion in this chat into a note for the blog. Never commits or pushes - that stays the user's own step.
---

# Teach me

This repo (`content/blogs/`) is the user's personal, Obsidian-linked notes-as-blog system: short topic write-ups (~2 min read, longer only when the topic genuinely needs it), interlinked with relative Markdown links, tagged for automatic "Related" surfacing, and backlinked automatically at build time. This skill runs the full loop end to end: **pick a topic → teach it in chat → write the note → place it correctly → branch it**. The user commits and pushes themselves — never do that as part of this skill.

## Flow

### 1. Establish the topic
- If the user gave a topic as an argument or in their message, use it.
- If not, ask what they want to learn. A vague area ("something about Kafka internals") is fine - narrow it together in the first reply rather than blocking on a fully-formed topic name.
- Briefly check `content/blogs/` (via a quick `ls`/`grep`) for whether this topic, or something adjacent, already has a note. If a close match exists, say so and ask whether this is a new angle (new note) or an update to the existing one.

### 2. Teach it - stay in this phase until the user signals otherwise
This is a real conversation, not a scripted Q&A. Adapt depth to what the user already knows (check memory/prior posts in this repo for their background - e.g. their existing Spring/Kafka/Java posts show senior backend experience, so don't over-explain fundamentals in that territory).

- Explain the core idea first, then go deeper where the user asks or where the failure modes/gotchas live - that's usually the highest-value 20% and what tutorials skip.
- Use concrete examples over abstract description. Reuse the user's own stack/examples when it helps (their posts lean Java/Spring/Kafka/Postgres).
- Ask questions back periodically to check understanding rather than only lecturing - this is what makes the resulting note something *they* actually understand later, not a transcript of you talking.
- Correct misconceptions directly and plainly when they surface.
- **Do not start writing the note yet.** Stay in discussion until the user gives a clear signal they're ready to wrap up: "let's write this up," "create the note," "I think I've got it," "summarize this," "done," or similar. If it's ambiguous, ask "ready to turn this into a note, or want to go deeper on anything first?" rather than guessing.

### 3. Write the note
Once the user signals readiness:

1. **Read 1-2 existing posts** in a similar category first (e.g. `content/blogs/kafka/apache-kafka-concepts/index.md` for a deep multi-section topic, or a flat file like `content/blogs/databases/postgres-gin-indexes-for-jsonb.md` for a short one) to match current frontmatter and prose conventions exactly - don't invent a new frontmatter shape.
2. **Frontmatter**: match the established fields - `draft`, `weight`, `showAuthor`, `showDate`, `showWordCount`, `showReadingTime`, `date` (today), `title`, `tags`, `categories`, and `mermaid: true` only if you actually use a diagram shortcode. Default `draft: false` since this is a topic the user just finished learning and chose to write up - only use `draft: true` if the user says the note is unfinished or they want to review before publishing.
3. **Length**: aim for a genuinely 2-minute read (roughly 400-600 words). Only go longer if the topic doesn't fit in that - if so, prefer the bundle pattern (`content/blogs/<category>/<topic>/index.md`) used by the Kafka post over one huge flat file, so it can later be split into linked leaf notes if needed.
4. **Open with a dense summary paragraph** (see the Kafka post's opening) that front-loads the key facts, not a throat-clearing intro.
5. **Interlink**: search existing notes for related concepts and link out with plain relative Markdown links, e.g. `[SOLID Principles](../basics/solid-principle.md)` - never `[[wikilink]]` syntax, it renders as literal text on the live site (Hugo can't parse it; see the render hook at `layouts/_default/_markup/render-link.html` for how these resolve). Reuse existing `tags`/`categories` vocabulary where it genuinely fits, since that's what drives the automatic "Related" section - check `grep -rho 'tags: \[.*\]' content/blogs` for the existing tag vocabulary before inventing new tags.
6. **Diagrams**: only use the `moving-diagram` or `back-of-envelope` shortcodes (see `layouts/shortcodes/`) or Mermaid when a picture genuinely clarifies a flow - not by default.
   - **Whenever the topic involves a flow of data** (a message/request moving between components over time - e.g. producer→broker→consumer, client→server→db, an event pipeline, a replication/election handoff), build the diagram the way `content/blogs/kafka/apache-kafka-concepts/index.md` does it: a **live `moving-diagram`** (animated boxes/wires/moves showing the data actually traveling) is required for that flow, not optional or a nice-to-have.
   - If the flow also has a clear ordered sequence of actor interactions (who calls/acks whom, in what order), pair it with a **Mermaid `sequenceDiagram`** placed immediately before the `moving-diagram` block - the sequence diagram gives the static step-by-step contract, the moving-diagram gives the animated feel of it happening. Not every flow needs the sequence diagram (skip it if there's no meaningful multi-actor ordering to show), but every data flow needs the live moving-diagram.
   - Set `mermaid: true` in frontmatter whenever a `{{< mermaid >}}` block is used.

### 4. Place it
- Look at the existing folders under `content/blogs/` (`ai`, `architecture`, `basics`, `databases`, `java`, `kafka`, `kubernetes`, `spring`, `system-design`, `tools`, ...) and pick the best fit by content, not by guessing from the topic name alone.
- If nothing fits, create a new category folder - don't force an unrelated topic into an existing one.
- Filename: kebab-case of the topic (`redis-pub-sub.md`), or `<topic>/index.md` if it's a bundle per point 3.3 above.

### 5. Branch it
Do this **before** or immediately after writing the file (either order is fine since uncommitted changes carry across a branch switch), but always:

1. `git status --porcelain` first. If there are unrelated uncommitted changes already sitting in the working tree, stop and ask the user how to handle them - don't silently carry someone else's in-progress work onto the new branch.
2. Branch from up-to-date `main`, not from whatever branch happens to be checked out:
   ```
   git fetch origin main
   git checkout -b learn/<topic-slug> origin/main
   ```
   Fall back to local `main` if the fetch fails (offline).
3. `<topic-slug>` is the kebab-case topic, matching the note's filename/folder where reasonable.

### 6. Hand back
Stop here. Report: the branch name, the file(s) created, which category they landed in, and any existing notes you linked to/from. Tell them to review the note, then `git add` / `git commit` / `git push` themselves when ready - **do not** run any of those three yourself, even if asked to "finish it up," unless the user explicitly says to commit or push in those words.

## Notes
- If the user invokes `/teach-me` again while already mid-discussion on a topic, treat it as "continue" rather than restarting - stay in whichever phase you were in.
- If they invoke it with something like `/teach-me write` or `/teach-me wrap up`, treat that as the phase-3 signal directly.
