---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-11-01T00:00:00+08:00
title: "Monolith or Microservices for a New Startup?"
tags: [system-design, microservices, domain-driven-design]
categories: [System Design]
mermaid: true
---

A new startup has three ways to ship its first product:

- **Monolith**: one deployable app. Modules call each other as plain in-process function calls.
- **Modular monolith**: still one deployable, but each module owns its own tables, and other modules reach it only through its public interface.
- **Microservices**: each part deploys on its own and talks to the rest over the network.

**At a new startup, start with one deployable and strict module lines, because your boundaries are guesses and moving one should cost a refactor, not a migration.** In year one the product changes every week, and code moves between modules a lot. Inside one deployable, moving a boundary is a refactor and one deploy. Across services, the same move needs an API change, a data migration and several deploys in a fixed order. I'll call that difference the boundary-move cost. Pull a service out when you can name the reason: very different resource needs, or a team with its own release schedule. Several teams on day one, working in a domain they already know, can justify a few services early. Whatever you pick, don't build a distributed monolith.

## The desk you keep moving

Think of moving a desk. Inside one house it's a ten-minute job. If every room were a separate building, the same move would need a van, a new address and a note to every visitor. In year one you move furniture a lot.

In code, the desk is a piece of logic and the rooms are modules. Say discounts start out in the orders module. A month later you learn that discounts depend on the payment method and refunds have to reverse them, so they belong in payments. Nobody got this wrong. Nobody knew it on day one. Fowler makes the same point in *MonolithFirst*: "even experienced architects working in familiar domains have great difficulty getting boundaries right at the beginning."[^dates]

## One boundary move, two ways

In a modular monolith, moving discounts means moving the code, moving the table into payments' schema, fixing the callers your compiler or tests find, and shipping one deploy. Across services, the move has to keep running callers working the whole time, so it becomes an expand-and-contract sequence:

{{< mermaid >}}
sequenceDiagram
  participant O as orders service
  participant P as payments service
  participant C as other callers
  Note over P: deploy 1: add discounts API v2 and table
  O->>P: backfill: copy existing discount rows
  Note over O: deploy 2: call payments v2, stop writing locally
  C->>P: callers move to payments for discounts
  Note over O: deploy 3 (later): drop old code and columns
{{< /mermaid >}}

*Figure 1: Across services the move has an order. Payments must ship the new API before orders can use it, and the cleanup waits until every caller has switched.*

The animation runs the same move both ways. Watch the deploy counters on the right.

{{< moving-diagram >}}
{
  "title": "Moving one boundary",
  "subtitle": "discounts moves from orders to payments",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 170,
  "boxes": {
    "orders1":   [80, 80, 240, 140, "orders", "discounts"],
    "payments1": [320, 80, 480, 140, "payments"],
    "users1":    [560, 80, 720, 140, "users"],
    "orders2":   [80, 240, 240, 300, "orders", "discounts"],
    "payments2": [320, 240, 480, 300, "payments"],
    "users2":    [560, 240, 720, 300, "users"]
  },
  "resize": [
    { "box": "orders1",   "start": 20,  "end": 21,  "to": [80, 80, 240, 140],   "sub": " " },
    { "box": "payments1", "start": 45,  "end": 46,  "to": [320, 80, 480, 140],  "sub": "discounts" },
    { "box": "orders2",   "start": 80,  "end": 81,  "to": [80, 240, 240, 300],  "sub": " " },
    { "box": "payments2", "start": 120, "end": 121, "to": [320, 240, 480, 300], "sub": "discounts" }
  ],
  "wires": [
    [[40,58],[760,58],[760,162],[40,162],[40,58]],
    [[240,110],[320,110]],
    [[480,110],[560,110]],
    [[240,270],[320,270]],
    [[480,270],[560,270]]
  ],
  "moves": [
    { "start": 20,  "end": 45,  "path": [[240,110],[320,110]], "color": "primary", "label": "discounts" },
    { "start": 50,  "end": 52,  "path": [[160,110],[160,111]], "color": "primary" },
    { "start": 50,  "end": 52,  "path": [[400,110],[400,111]], "color": "primary" },
    { "start": 50,  "end": 52,  "path": [[640,110],[640,111]], "color": "primary" },
    { "start": 65,  "end": 67,  "path": [[160,270],[160,271]], "color": "secondary" },
    { "start": 65,  "end": 67,  "path": [[400,270],[400,271]], "color": "secondary" },
    { "start": 80,  "end": 120, "path": [[240,270],[320,270]], "color": "secondary", "label": "discounts" },
    { "start": 125, "end": 127, "path": [[400,270],[400,271]], "color": "secondary" },
    { "start": 150, "end": 152, "path": [[160,270],[160,271]], "color": "secondary" }
  ],
  "tags": [
    { "start": 0,   "end": 250, "x": 130, "y": 44,  "text": "modular monolith", "color": "primary" },
    { "start": 0,   "end": 250, "x": 280, "y": 128, "text": "in-process", "color": "primary" },
    { "start": 0,   "end": 50,  "x": 690, "y": 44,  "text": "deploys: 0", "color": "primary" },
    { "start": 50,  "end": 250, "x": 690, "y": 44,  "text": "deploys: 1", "color": "primary" },
    { "start": 0,   "end": 250, "x": 120, "y": 222, "text": "microservices", "color": "secondary" },
    { "start": 0,   "end": 250, "x": 280, "y": 290, "text": "network", "color": "secondary" },
    { "start": 0,   "end": 125, "x": 690, "y": 222, "text": "deploys: 0", "color": "secondary" },
    { "start": 125, "end": 150, "x": 690, "y": 222, "text": "deploys: 1", "color": "secondary" },
    { "start": 150, "end": 250, "x": 690, "y": 222, "text": "deploys: 2", "color": "secondary" },
    { "start": 65,  "end": 160, "x": 400, "y": 335, "text": "API v2 + data migration", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 20,  "text": "same move: discounts goes from orders to payments", "color": "primary" },
    { "start": 20,  "end": 65,  "text": "one deployable: a refactor, then one deploy", "color": "primary" },
    { "start": 65,  "end": 125, "text": "services: a new API version and a data migration", "color": "secondary" },
    { "start": 125, "end": 175, "text": "payments deploys first, then orders", "color": "secondary" },
    { "start": 175, "end": 999, "text": "Early on, keep boundary moves cheap", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

*Figure 2: The top row finishes with one deploy. The bottom row moves the same code but needs two deploys in order, plus the cleanup from Figure 1.*

The network hop itself is cheap to draw and expensive to run. A datacenter round trip is about 0.5 ms, roughly 5,000 RAM reads, as the [latency numbers](../latency-numbers/) note explains. The bigger cost here is coordination, though. Two deploys in a fixed order, a backfill that has to be checked, and a period where both code paths are live.

## What keeps a monolith modular

One deployable only stays cheap to change if the module lines hold. The rule from the post does most of the work: **never let one module read another's tables.** If orders runs SQL against the payments tables, the tables are now a public API that nobody agreed to, and moving discounts later means finding every query that touches them.

Shopify's main Rails app is the best-known large case. By 2016 it had become fragile, with "new code having unexpected repercussions". The fix wasn't to split it into services. Kirsten Westeinde's 2019 post describes sorting about 6,000 Ruby classes into components named after business domains such as orders, shipping and billing, all still shipped as one app worked on by over a thousand developers. A CI tool called Wedge traced calls and flagged any that crossed into another component without going through its public interface.[^wedge] Shopify also open-sourced Packwerk, a gem that groups files into packages and flags references to another package's private constants.

You don't need Shopify's tooling on day one. A folder per module, a public interface file for each, and a lint or architecture test that fails the build on a cross-module import or table read get you most of the way. Domain names from [domain-driven design](../../architecture/domain-driven-design-basics.md) make good module names, since they follow how the business talks.

A stateless monolith also scales out. Run more copies behind a load balancer, as the [vertical vs horizontal scaling](../vertical-vs-horizontal-scaling/) note shows. Splitting into services doesn't add capacity by itself. The [Day 4 note on microservices and scale](../microservices-and-scale/) covers that argument and the Prime Video case, so I won't repeat it here.

## Putting a number on it

The boundary-move cost only counts if you move boundaries often, so it's worth a rough estimate. The defaults below are my guesses for an early-stage team, not measurements. Replace them with your own.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Your guesses",
      "inputs": [
        { "id": "moves", "label": "Boundary moves per month", "default": 2, "step": 1 },
        { "id": "daysMono", "label": "Engineer-days per move, one deployable", "default": 1, "step": 0.5 },
        { "id": "daysSvc", "label": "Engineer-days per move, across services", "default": 5, "step": 0.5 },
        { "id": "services", "label": "Number of services", "default": 8, "step": 1 },
        { "id": "upkeepH", "label": "Upkeep per deployable (hours/week)", "default": 2, "step": 0.5, "unit": "h" }
      ]
    },
    {
      "title": "Engineer-days per year",
      "outputs": [
        { "id": "monoMoves", "label": "Moving boundaries, one deployable", "formula": "moves * 12 * daysMono", "format": "number" },
        { "id": "svcMoves", "label": "Moving boundaries, services", "formula": "moves * 12 * daysSvc", "format": "number" },
        { "id": "monoUpkeep", "label": "Upkeep, one deployable", "formula": "upkeepH * 52 / 8", "format": "number" },
        { "id": "svcUpkeep", "label": "Upkeep, services", "formula": "services * upkeepH * 52 / 8", "format": "number" },
        { "id": "gap", "label": "Extra days per year for services", "formula": "(moves * 12 * daysSvc + services * upkeepH * 52 / 8) - (moves * 12 * daysMono + upkeepH * 52 / 8)", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

*Figure 3: With the defaults, services cost 120 days of boundary moves and 104 days of upkeep a year, against 24 and 13 for one deployable.*

The model treats every move as costing the same, counts upkeep (pipelines, dashboards, alerts, on-call) as a flat number of hours per deployable, and ignores what services might save you. Check it by hand: 2 × 12 × 5 = 120, and 8 × 2 × 52 / 8 = 104, so the gap is 224 − 37 = 187 engineer-days, close to a full year of one engineer.[^days] Set moves per month to zero and most of that gap goes away. That's the honest reading of this calculator. One deployable wins on boundary-move cost exactly when boundaries are still moving.

## The case for starting with services

The strongest case for starting with services comes from Stefan Tilkov, in a reply published on Fowler's own site six days after *MonolithFirst*. His argument: it's "extremely hard to split up an existing monolith into separate pieces", because a monolith's parts end up sharing domain objects, persistence models and transactions. Starting a system is the best moment to draw hard lines, and a network boundary is a line nobody crosses by accident. He'd start with services when the team knows the domain well, for example when rebuilding an existing system, and when the system is big enough to pay for the overhead.

That holds in the situations he names. A team rebuilding a product it has run for years isn't guessing at boundaries. Several teams on day one need separate release schedules from the start. For them, the boundary-move cost is low because the boundaries rarely move.

It doesn't fit engineer #1 at a new startup. The domain isn't known yet, and Tilkov concedes the cost himself: with services, "refactoring in the large becomes much harder." His worry about entanglement is real, but it's an argument for enforced module lines, not for the network. Fowler's own evidence is anecdotal, and he says so. His pattern is that almost all the successful microservice stories he'd heard "started with a monolith that got too big and was broken up", and he adds that "the evidence is sparse". Treat both essays as experienced opinion, not data.

## When one deployable is the wrong call

One deployable stops being the right answer when you can name a reason it hurts:

- **Very different resource needs.** A video transcoder wants GPUs and can wait in a queue. Checkout wants low latency and must stay up. In one process, a transcoding spike slows checkout.
- **A team with its own release schedule.** If one team's broken test keeps holding up another team's deploy every week, separate pipelines fix exactly that.

The modular monolith also fails in a known way. The lines stop being enforced, someone adds one cross-module query "just for now", and in two years you have the fragile app Shopify described. You'll see it as changes that touch five modules for one feature.

The worst outcome is the distributed monolith: services that share a database and must deploy together. You pay the network costs of microservices and keep the coupling of a monolith.

{{< moving-diagram >}}
{
  "title": "The distributed monolith",
  "subtitle": "two services, one shared database",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 225,
  "posterFrame": 150,
  "boxes": {
    "orders":   [60, 60, 220, 130, "orders svc"],
    "payments": [580, 60, 740, 130, "payments svc"],
    "db":       [320, 230, 480, 300, "shared DB", "discounts table"]
  },
  "wires": [
    [[140,130],[140,265],[320,265]],
    [[660,130],[660,265],[480,265]]
  ],
  "moves": [
    { "start": 15,  "end": 50,  "path": [[140,130],[140,265],[320,265]], "color": "primary", "label": "rename column" },
    { "start": 70,  "end": 100, "path": [[660,130],[660,265],[480,265]], "color": "primary", "label": "old query" },
    { "start": 102, "end": 132, "path": [[480,265],[660,265],[660,130]], "color": "secondary", "label": "error" },
    { "start": 150, "end": 152, "path": [[140,95],[140,96]], "color": "secondary" },
    { "start": 150, "end": 152, "path": [[660,95],[660,96]], "color": "secondary" }
  ],
  "tags": [
    { "start": 150, "end": 225, "x": 400, "y": 100, "text": "deploy both together", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 60,  "text": "orders ships a schema change on its own", "color": "primary" },
    { "start": 60,  "end": 140, "text": "payments still reads the old column, and breaks", "color": "secondary" },
    { "start": 140, "end": 999, "text": "every schema change now needs a joint deploy", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 4: The services deploy separately in theory, but the shared table ties them together. A change on one side breaks the other until both ship.*

Database-per-service is the fix, and the [microservices fundamentals](../../architecture/microservices-fundamentals.md) note covers why. It's the same rule as in the modular monolith: a module's tables are private.

## What to measure

You can find out which case you're in instead of arguing about it:

- **Boundary moves per month.** Count merged changes that move code or tables between modules. If it's near zero for a quarter, your boundaries have settled and a split costs less.
- **Cross-module violations.** A lint or a Packwerk-style check gives you a count. It should be zero and stay there.
- **Deploy blocking.** How often does one team's change hold up another team's release? This is the number that justifies a service.
- **Lockstep deploys.** If two services keep shipping together, you have a distributed monolith, and merging them back may be cheaper than untangling the database.

## References

**Essays**
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html), Martin Fowler, June 2015.
- [Don't start with a monolith](https://martinfowler.com/articles/dont-start-monolith.html), Stefan Tilkov, June 2015.
- [Microservice Premium](https://martinfowler.com/bliki/MicroservicePremium.html), Martin Fowler, May 2015.

**Case studies and tools**
- [Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), Kirsten Westeinde, Shopify Engineering, February 2019.
- [Packwerk](https://github.com/Shopify/packwerk), Shopify's gem for enforcing package boundaries in Rails apps.

[^dates]: *MonolithFirst* is from 3 June 2015. Fowler's *Microservice Premium*, three weeks earlier, makes the cost side of the argument: services bring automated deployment, monitoring, failure handling and eventual consistency, and "the majority of software systems should be built as a single monolithic application."
[^wedge]: The 2019 post describes Wedge flagging violations and scoring each component, not blocking them. Making each component load only its declared dependencies was still a plan under research then.
[^days]: 187 engineer-days is a lot of precision for a model built on guesses. Read it as "a large fraction of one engineer's year", not as a forecast.
