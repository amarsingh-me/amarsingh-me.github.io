# Article quality rubric

Total = mechanical (35, from `scripts/quality_check.py`) + judged items (65, below). Pass mark: 85.

For each item, give full, partial or zero credit using the bands. When an article sits between two bands, use the lower one. Every score needs a one-line reason that points at the text.

| Item | long | short |
|---|---|---|
| 1. Thesis early and clear | 10 | 15 |
| 2. Evidence | 15 | 10 |
| 3. Fair counterargument | 8 | 5 |
| 4. When not to use it / failure modes | 10 | 10 |
| 5. Calibrated confidence | 5 | 5 |
| 6. Diagrams explain how the thing works | 10 | 5 |
| 7. One idea, named and reused | 4 | 10 |
| **Total** | **65** | **65** |

## 1. Thesis early and clear
- **Full**: The opening summary states the conclusion as a claim you could disagree with. The bold line repeats it in the article's own words. A reader who stops after the first paragraph still knows the answer.
- **Half**: The conclusion is there, but it's buried mid-paragraph, hedged into mush, or only shows up after the first section.
- **Zero**: The opening only sets up the topic ("In this post we'll look at…"), or there's no single claim.

## 2. Evidence
- **Full**: Every main claim rests on at least one of these: a number with units, a worked calculation (`back-of-envelope`), a named real case, or a concrete example. There are 2+ different examples that show what they have in common. The numbers are plausible and consistent across the text, the calculator and the diagrams.
- **Half**: Some claims are backed. Others are just asserted, or there's only one example.
- **Zero**: It's assertion and analogy throughout.

## 3. Fair counterargument
- **Full**: It states the strongest opposing view in a form its supporters would accept, then says where it holds and where it doesn't.
- **Half**: The other side gets a mention but is a straw man or gets brushed off in one line.
- **Zero**: There's no opposing view.

## 4. When not to use it / failure modes
- **Full**: It gives concrete conditions under which the advice is wrong, and how it fails (what breaks, what you'd see), plus what to measure to know which case you're in.
- **Half**: The limits are generic ("it depends", "not always").
- **Zero**: The idea is presented as always right.

## 5. Calibrated confidence
- **Full**: Hedges match the evidence. Measured things are stated plainly, and opinions and thin evidence are marked as such ("in my experience", "the evidence here is thin"). There's no overclaiming and no reflexive hedging.
- **Half**: There's some overclaiming ("always", "never") or a lot of needless hedging.
- **Zero**: Opinion is presented as fact throughout.

## 6. Diagrams explain how the thing works
- **Full**: Every block shows a mechanism the prose relies on: the data moving, the order of calls, the calculation. The text around it tells the reader what to watch. Each caption names that takeaway. For `short`: either a useful diagram, or no diagram at all when the topic has no flow (that still earns full credit).
- **Half**: A diagram repeats the prose without adding anything, or there's no guidance on what to notice.
- **Zero**: Decorative diagrams. Or, for `long`, a data flow described in prose with no diagram.

## 7. One idea, named and reused
- **Full**: The post is about one idea. It has a short noun-phrase name (e.g. "retry amplification", "the microservice premium"), and once the term is named it's always used the same way.
- **Half**: There's one idea, but the name drifts between synonyms. Or there are two ideas competing for the post.
- **Zero**: It's a grab bag of loosely related points.
