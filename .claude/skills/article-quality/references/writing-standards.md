# Writing standards: how the best technical bloggers write

This is where the rubric comes from. Martin Fowler's pages were read directly (sources at the bottom). The notes on other writers come from their own posts about writing and from how their published work looks.

## Fowler's long-form article (the `long` profile)

From *Microservices* (Lewis & Fowler, 2014):

1. A title plus a one-line subtitle that defines the term ("a definition of this new architectural term").
2. An italic abstract that gives the whole argument up front.
3. A byline with the date and topic tags.
4. A table of contents for long pieces.
5. An introduction that defines the term and contrasts it with the alternative (microservices vs. monolith).
6. H2 sections, with the named characteristics as H3s ("Design for failure").
7. Sidebars: asides phrased as questions ("How big is a microservice?"), kept out of the main thread.
8. Numbered figures with captions.
9. Block quotes with attribution (Conway, 1968).
10. A closing section that looks ahead with caution ("Are Microservices the Future?").
11. Footnotes for asides, credits and small jokes.
12. References grouped by type: articles, books, talks, papers.
13. A revision history. Fowler calls this an *Evolving Publication*: the article keeps being updated.

## Fowler's bliki post (the `short` profile)

From *MonolithFirst* (about 900 words):

1. It opens with something he has seen ("I've been hearing stories…"), not with a definition.
2. A short numbered list of the observation, then the thesis in **bold**.
3. Reasons, then options, then a fair statement of the opposing view, then a tentative close.
4. Dense links to other entries. Each post explains one idea and links to the rest.
5. Footnotes and named acknowledgements.

## Qualities shared by the best writers

**Clear thinking**
1. One idea per post, with a name you can reuse. Fowler: "short, evocative noun-phrase names" become shared vocabulary.
2. The thesis comes early. The abstract or bold line gives the conclusion before the argument.
3. They say when *not* to use it: the forces and the contra-indications. There's no "one true way".
4. They steelman the opposing view before qualifying their own position.
5. Calibrated confidence: "we think", "tend to", "I don't have enough anecdotes yet". Julia Evans says plainly what she doesn't know and doesn't hedge what she does know.
6. They write from their own experience. Evans: "write for a past version of myself."
7. Fundamentals over fashion, so posts still hold up years later.

**Evidence**

8. Concrete examples, more than one, so the reader can see what they have in common. Code samples are kept simple and skippable.
9. Numbers and measurement. Dan Luu, Brendan Gregg and Marc Brooker back claims with data, latency figures or back-of-envelope estimates.
10. They're honest about how good the evidence is. Fowler says outright when his evidence is "sparse".

**Reader experience**

11. A conversational first person, the way engineers talk to each other.
12. Diagrams that explain how the thing works: Fowler's numbered figures, Evans's comics, the interactive explainers by Bartosz Ciechanowski and Sam Who.
13. A structure readers can skim: headings, sidebars for side topics, footnotes for asides.
14. They write soon after learning something, while they still remember what confused them.

**Craft and trust**

15. Reviewers and acknowledgements, named.
16. Revisions in public: a revision history, and the old version kept when a rewrite goes deep.
17. Links to other posts, so each post sits in a web of related ideas.
18. Further reading and references, grouped.
19. Light humour in the footnotes, never in the core argument.
20. Form serves content. Leave out a section rather than fill it with weak text. Prose usually beats too many headings.

## Adapted for this site

- Revision history and sidebars are optional. References and footnotes are required.
- The italic abstract is the site's existing "dense summary paragraph" opening (see `teach-me`).
- "Numbered figures" means a `*Figure N: …*` caption under each `moving-diagram`, Mermaid or `back-of-envelope` block.

## Sources
- https://martinfowler.com/articles/microservices.html
- https://martinfowler.com/bliki/MonolithFirst.html
- https://martinfowler.com/articles/writingPatterns.html
- https://martinfowler.com/bliki/EvolvingPublication.html
- https://jvns.ca/blog/2017/03/20/blogging-principles/
- https://jvns.ca/blog/2021/05/24/blog-about-what-you-ve-struggled-with/
- https://jvns.ca/blog/2023/08/07/tactics-for-writing-in-public/
