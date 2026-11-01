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

A module boundary is the line that decides which module or service owns a piece of logic and its tables. **At a new startup, start with a modular monolith, because the lines between your modules or services are guesses, so moving one has to stay as cheap as a refactor.** If discounts move from orders to payments, one deployable needs a refactor and one deploy. Separate services need a new API, a data migration and a release from every caller. I'll call the price of that move the boundary-move cost. In year one you move these lines often, so you'd pay a high boundary-move cost again and again.

The exception is several teams building a product they've built before: they know where the lines go, so the lines rarely move, and separate services let each team ship on its own.

## The desk you keep moving

Think of moving a desk. Inside one house it's a ten-minute job. If every room were a separate building, the same move would need a van, a new address and a note to every visitor.

Each part of that picture has a counterpart in code:

- **The desk** is a piece of logic plus its tables: discounts.
- **The house** is one deployable, and **the rooms** are its modules: orders, payments, users.
- **The ten-minute move** is a refactor: move the discount code and table into payments, run the tests, ship one deploy.
- **A separate building** is a separate service with its own deploy and its own database.
- **The van** is the network, which every call to discounts now crosses instead of making an in-process function call.
- **The new address** is the new API endpoint that payments has to publish for discounts.
- **The note to every visitor** is every caller of discounts changing its code to use that endpoint and shipping.

In year one you move furniture a lot, because the product is still taking shape. Discounts start out in orders, then you learn that they depend on the payment method and that refunds must reverse them, so they belong in payments. Nobody could know that on day one. Fowler makes the same point in *MonolithFirst*: "even experienced architects working in familiar domains have great difficulty getting boundaries right at the beginning."[^dates]

## Moving discounts, two ways

In a modular monolith, moving discounts means moving the code and table into payments, fixing the callers your tests find, and shipping one deploy. Across services, running callers keep calling orders for discounts during the move, so they must keep working throughout. That makes it an expand-and-contract sequence:

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

The animation runs the move both ways; watch the deploy counters.

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

After the move, every discount call from orders crosses the network to payments: about 0.5 ms, roughly 5,000 RAM reads (see the [latency numbers](../latency-numbers/) note). The coordination costs more than the hop. Payments has to deploy before orders, someone has to check that the backfill copied every discount row, and both code paths stay live until the last caller has switched.

## What keeps a monolith modular

One deployable only stays cheap to change if no module reaches into another module's code or tables. The post's rule does most of the work: **never let one module read another's tables.** If orders runs SQL against the payments tables, those tables become a public API nobody agreed to, so moving discounts later means finding every query that touches them.

Shopify's Rails app is the best-known case. By 2016 it was fragile, with "new code having unexpected repercussions". Kirsten Westeinde's 2019 post describes how Shopify kept one app, worked on by over a thousand developers, and sorted about 6,000 Ruby classes into domain components such as orders, shipping and billing. A CI tool called Wedge traced calls and flagged, without blocking, any that entered another component without going through its public interface. Shopify later open-sourced Packwerk, a gem that flags references to another package's private constants.

On day one, a folder per module, a public interface for each, and a test that fails the build on a cross-module import or table read get you most of the way. Name modules after business areas, as in [domain-driven design](../../architecture/domain-driven-design-basics.md), because those names follow how the business talks.

Traffic doesn't force a split, because a stateless monolith [scales out](../vertical-vs-horizontal-scaling/) behind a load balancer; the [Day 4 note](../microservices-and-scale/) covers why.

## The case for starting with services

The strongest case for starting with services comes from Stefan Tilkov, in a reply on Fowler's site six days after *MonolithFirst*. It's "extremely hard to split up an existing monolith into separate pieces", he argues, because its parts end up sharing domain objects, persistence models and transactions. So the start is the best moment to draw hard lines between parts, since no developer crosses a network boundary by accident. He'd start with services when the team knows the domain and the system is big enough to pay the overhead.

That's the exception the post names, and it needs both conditions. You've built this kind of product before, so you know discounts belong in payments, so the lines between services rarely move and the boundary-move cost rarely gets paid. And you start with several teams, so each gains from deploying its own service on its own schedule, and that gain pays for the services' upkeep from day one. Without either condition the case fails: several teams on a new product pay the cross-service price for every move, and a single team on a known product gets no independent-deploy gain to cover the upkeep.

It doesn't fit engineer #1 at a new startup, because there's one team and the product hasn't been built before. Tilkov concedes that with services "refactoring in the large becomes much harder." His worry that modules get entangled is real, but enforced module lines answer it inside one deployable, as Shopify's Wedge did, without a network hop. Fowler says his own evidence is anecdotal: almost all the successful microservice stories he'd heard "started with a monolith that got too big and was broken up", and "the evidence is sparse". Read both essays as experienced opinion.

## When one deployable is the wrong call

Split out a service when you can name one of these reasons:

- **Very different resource needs.** A video transcoder wants GPUs and can wait; checkout wants low latency. In one process they share CPU and memory, so a transcoding spike slows checkout.
- **A team with its own release schedule.** If one team's broken test holds up another team's deploy every week, separate pipelines fix that.

A modular monolith fails when the build stops enforcing module lines: one cross-module query added "just for now" becomes many, until one feature touches five modules and you have the fragile app Shopify described.

The worst outcome is the distributed monolith: services that share a database, so they must deploy together. You pay the network cost of microservices and keep the coupling of a monolith.

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

*Figure 3: The services deploy separately in theory, but the shared table ties them together. A change on one side breaks the other until both ship.*

The fix is a database per service, which keeps deploys independent, as the [microservices fundamentals](../../architecture/microservices-fundamentals.md) note explains. It's the modular monolith's rule again: a module's tables are private.

## What to measure

Measure which case you're in:

- **Boundary moves per month.** Count merged changes that move code or tables between modules, per module. If a module has had no moves in or out for a quarter, its boundary has stopped moving, so splitting it into a service now costs one expand-and-contract instead of one every month.
- **Cross-module violations.** A lint or Packwerk-style check counts them. Keep it at zero, because each one is a hidden dependency a later move must untangle.
- **Deploy blocking.** How often one team's change holds up another team's release. This number justifies a service.
- **Lockstep deploys.** Two services that keep shipping together are a distributed monolith, so merging them may be cheaper than untangling the database.

## My vote

Build one deployable with a module per business area and no module reading another's tables, so moving logic like discounts stays a refactor and one deploy. When a module has had no moves for a quarter and you can name a reason, such as GPU-hungry work or a team with its own release schedule, pull it out as a service with its own API and database, and pay the expand-and-contract cost once.

My vote: a modular monolith first. Split out a service once its boundary has stopped moving.

## References

**Essays**
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html), Martin Fowler, June 2015.
- [Don't start with a monolith](https://martinfowler.com/articles/dont-start-monolith.html), Stefan Tilkov, June 2015.
- [Microservice Premium](https://martinfowler.com/bliki/MicroservicePremium.html), Martin Fowler, May 2015.

**Case studies and tools**
- [Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), Kirsten Westeinde, Shopify Engineering, February 2019.
- [Packwerk](https://github.com/Shopify/packwerk), Shopify's gem for enforcing package boundaries in Rails apps.

[^dates]: *MonolithFirst* is from 3 June 2015. Three weeks earlier, Fowler's *Microservice Premium* argued that "the majority of software systems should be built as a single monolithic application."
