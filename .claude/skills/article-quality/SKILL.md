---
name: article-quality
description: Score a blog post in content/blogs/ against the writing standard of the best technical bloggers (Martin Fowler's article and bliki formats, Julia Evans, Dan Luu), then rewrite it in up to 3 passes until it scores 85/100 or better. Score = mechanical checks from a script (35) + a judged rubric (65). Use after writing any new article or note (long-form handoff articles, teach-me notes, hand-written posts), before humanizing it. Also use when the user says "check the article quality", "score this post", "does this match the format", or invokes /article-quality.
---

# Article quality

Every new post on this site is held to one standard, taken from how Martin Fowler, Julia Evans and similar writers work. `references/writing-standards.md` explains where the rules come from. `references/rubric.md` turns them into points. Read both before your first scoring in a session.

The score is out of 100:
- **Mechanical (35)**: `scripts/quality_check.py` checks the frontmatter, the summary opening, the bold thesis, word count, figure captions, the limits section, references, footnotes and interlinks.
- **Rubric (65)**: you judge the thesis, the evidence, the counterargument, when not to use it, calibrated confidence, the diagrams, and whether the post sticks to one named idea.

## Workflow

1. **Pick the profile.**
   - `long`: Fowler's article format. Use it for a bundle (`<slug>/index.md`) or a post over 900 words. Every long-form handoff article uses `long`.
   - `short`: bliki format. Use it for flat notes of about 400–700 words, e.g. teach-me notes.

   The script picks the profile automatically. Pass `--profile` when the caller names one.
2. **Mechanical score.**
   ```
   python3 .claude/skills/article-quality/scripts/quality_check.py <file> [--profile long|short]
   ```
   The script prints JSON with `mechanical` (out of 35) and one entry per check, giving its `points`, `max` and a `detail` that says what's wrong.
3. **Rubric score.** Score each item in `references/rubric.md` for the profile. Give every score a one-line reason that quotes or points at the article. Don't award points for something the article doesn't actually do.
4. **Total and gaps.** Total = mechanical + rubric. List the gaps by points lost, biggest first.
5. **Rewrite loop.** If the total is under 85:
   - Fix the gaps, worst first, editing the article in place.
   - Re-run the script and re-score the rubric.
   - Keep a pass only if the total goes up. If it doesn't, revert that pass and try a different fix.
   - Stop at 85 or above, or after **3 passes**, whichever comes first. Never run more than 3.
6. **Hard rules for every rewrite.**
   - Never invent facts, numbers, quotes, sources, case studies or reviewers. If a gap needs evidence you don't have, say so in the report and leave the gap open.
   - When the post came from a LinkedIn brief, keep the brief's `definitions` and analogy exactly.
   - Don't edit the JSON inside `moving-diagram` or `back-of-envelope` blocks to raise the score. Captions go *under* a block, never inside it.
   - Add a reference only if it's a URL you've read in this session or one the article already cites. A missing reference costs fewer points than a wrong one.
   - Footnotes are for real asides: a caveat, a credit, the source of a number. They're not for padding.
7. **Humanize last.** After the loop, run the `humanize-writing` skill on the prose. Then re-run the script once. If humanizing broke a mechanical check (a dropped caption, a lost bold thesis), fix that check directly and don't start a new loop.
8. **Report.**
   ```
   Profile: long
   | Pass   | Mechanical | Rubric | Total |
   | start  | 14 / 35    | 41 / 65 | 55   |
   | pass 1 | 29 / 35    | 50 / 65 | 79   |
   | pass 2 | 33 / 35    | 54 / 65 | 87 ✓ |
   Remaining gaps: evidence (-4: no measured numbers for X), ...
   ```
   A caller that needs JSON (the long-form-writer agent) uses `quality_score` (the final total), `quality_passes` (the totals in order, start first) and `quality_gaps` (short strings).

## Format conventions the script looks for

- **Summary**: the intro before the first `##` has at least 60 words and gives the conclusion, not a warm-up. A short bullet list inside it (e.g. naming the kinds of a concept) is fine.
- **Bold thesis**: one claim of 5+ words in `**bold**` within the first 3 prose paragraphs. Bolding a single term doesn't count.
- **Figure captions**: on the first non-blank line after each `{{< /moving-diagram >}}`, `{{< /mermaid >}}` or `{{< /back-of-envelope >}}`, write an italic line `*Figure N: what the reader should notice.*`. Number the figures 1, 2, 3 in order.
- **Limits section**: an `##` heading such as "When it's the wrong call", "Trade-offs", "Limits" or "Failure modes".
- **References**: a closing `## References` (or `## Further reading`) with at least 3 links for `long`, or 1 for `short`. Group them by type (articles, books, talks, papers) when there are several.
- **Footnotes**: Goldmark syntax, i.e. `[^1]` in the text and `[^1]: …` at the bottom. Hugo renders these natively. Every reference needs a definition and every definition needs a reference.
- **Interlinks**: at least 1 relative Markdown link to another note, such as `[Kafka](../../kafka/apache-kafka-concepts/index.md)`. Never use `[[wikilinks]]`.
