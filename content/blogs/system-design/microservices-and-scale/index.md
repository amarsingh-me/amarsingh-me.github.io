---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-26T00:00:00+08:00
title: "Myth: Microservices Make You Scale Better"
tags: [system-design, microservices, distributed-systems]
categories: [System Design]
---

"Scale" covers two different problems:

- **Traffic scale**: handling more requests per second.
- **Team scale**: letting more engineers ship without stepping on each other.

A **monolith** is one deployable application whose modules call each other through plain function calls. A **microservice** deploys on its own and talks to the others over the network. **Splitting into microservices mostly helps team scale, not traffic scale.** Deploying separately gives no request more CPU. It lets the payments team release on Tuesday without waiting for the search team. A stateless monolith already scales out: run ten copies behind a load balancer. Split it only when one part needs very different resources, or when teams keep blocking each other's deploys.

## The same request, two ways

Take an order that touches orders, payments and users. In the monolith the client makes one network call, and the rest are function calls that cost nanoseconds and can't time out. Split the code into three services and every arrow becomes a network hop with its own timeout and retry policy. The animation runs both versions side by side.

{{< moving-diagram >}}
{
  "title": "Microservices and scale",
  "subtitle": "Same request, one process vs three services",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 160,
  "boxes": {
    "client1":   [30, 80, 150, 136, "client"],
    "orders1":   [240, 80, 360, 136, "orders"],
    "payments1": [430, 80, 550, 136, "payments"],
    "users1":    [620, 80, 740, 136, "users"],
    "client2":   [30, 230, 150, 286, "client"],
    "orders2":   [240, 230, 360, 286, "orders"],
    "payments2": [430, 230, 550, 286, "payments"],
    "users2":    [620, 230, 740, 286, "users"]
  },
  "wires": [
    [[150,98],[240,98]],
    [[240,118],[150,118]],
    [[360,108],[430,108]],
    [[550,108],[620,108]],
    [[150,248],[240,248]],
    [[240,268],[150,268]],
    [[360,248],[430,248]],
    [[430,268],[360,268]],
    [[550,248],[620,248]],
    [[620,268],[550,268]]
  ],
  "moves": [
    { "start": 15,  "end": 30,  "path": [[150,98],[240,98]], "color": "primary", "label": "request" },
    { "start": 31,  "end": 37,  "path": [[360,108],[430,108]], "color": "secondary", "label": "fn call" },
    { "start": 38,  "end": 44,  "path": [[550,108],[620,108]], "color": "secondary", "label": "fn call" },
    { "start": 50,  "end": 65,  "path": [[240,118],[150,118]], "color": "primary", "label": "response" },

    { "start": 15,  "end": 30,  "path": [[150,248],[240,248]], "color": "primary", "label": "hop 1" },
    { "start": 33,  "end": 48,  "path": [[360,248],[430,248]], "color": "primary", "label": "hop 2" },
    { "start": 50,  "end": 62,  "path": [[550,248],[592,248]], "color": "secondary", "label": "hop 3" },
    { "start": 75,  "end": 90,  "path": [[550,248],[620,248]], "color": "primary", "label": "retry" },
    { "start": 95,  "end": 108, "path": [[620,268],[550,268]], "color": "primary", "label": "response" },
    { "start": 110, "end": 123, "path": [[430,268],[360,268]], "color": "primary", "label": "response" },
    { "start": 125, "end": 138, "path": [[240,268],[150,268]], "color": "primary", "label": "response" }
  ],
  "tags": [
    { "start": 0,   "end": 250, "x": 90,  "y": 66,  "text": "monolith", "color": "primary" },
    { "start": 0,   "end": 250, "x": 490, "y": 160, "text": "one process: function calls inside", "color": "secondary" },
    { "start": 0,   "end": 250, "x": 90,  "y": 216, "text": "microservices", "color": "primary" },
    { "start": 0,   "end": 15,  "x": 680, "y": 66,  "text": "network calls: 0", "color": "primary" },
    { "start": 15,  "end": 250, "x": 680, "y": 66,  "text": "network calls: 1", "color": "primary" },
    { "start": 65,  "end": 250, "x": 90,  "y": 156, "text": "done", "color": "primary" },
    { "start": 0,   "end": 15,  "x": 680, "y": 216, "text": "network calls: 0", "color": "primary" },
    { "start": 15,  "end": 33,  "x": 680, "y": 216, "text": "network calls: 1", "color": "primary" },
    { "start": 33,  "end": 50,  "x": 680, "y": 216, "text": "network calls: 2", "color": "primary" },
    { "start": 50,  "end": 75,  "x": 680, "y": 216, "text": "network calls: 3", "color": "primary" },
    { "start": 75,  "end": 250, "x": 680, "y": 216, "text": "network calls: 4", "color": "primary" },
    { "start": 62,  "end": 80,  "x": 585, "y": 308, "text": "timeout · retry", "color": "secondary" },
    { "start": 138, "end": 250, "x": 90,  "y": 306, "text": "done", "color": "primary" }
  ],
  "captions": [
    { "start": 0,   "end": 15,  "text": "Same request, two designs", "color": "primary" },
    { "start": 15,  "end": 50,  "text": "monolith: one network call, then function calls", "color": "primary" },
    { "start": 50,  "end": 95,  "text": "microservices: a hop per service, and one times out", "color": "secondary" },
    { "start": 95,  "end": 150, "text": "after the retry, responses hop back one by one", "color": "primary" },
    { "start": 150, "end": 999, "text": "Splitting adds network hops, not capacity", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 1: The same request as one process (top) and as three services (bottom). Only the bottom row pays for hops and a retry.*

## Why splitting doesn't add capacity

Capacity comes from machines. Ten copies of a stateless monolith give you ten copies of orders, payments and users, as far as the database allows. That's plain [horizontal scaling](../vertical-vs-horizontal-scaling/), and it doesn't care whether the code inside is one module or forty.

Splitting adds work on top. Every call gets serialized, sent and parsed, and then the response makes the same trip back. Inside one data center a hop costs around a millisecond or a few, plus the tail.[^hop] As the [Latency vs Throughput](../latency-vs-throughput/) note explains, a request that crosses five services waits on the slowest of five p99s. Services that skip connection pooling also pay for TCP and TLS handshakes again and again, as the [URL to first byte](../how-a-url-becomes-a-webpage/) note shows.

Failure multiplies too. If each service is up 99.9% of the time and a request needs four in a row, it succeeds 99.6% of the time,[^avail] which is about four times the downtime.

Retries are worse. If every caller retries a failed call twice, each layer multiplies the calls below it by three. When the last of four services goes down, it takes 3 × 3 × 3 = 27 calls for one user click, right when it's trying to recover. The animation shrinks this to three services and one retry each:

{{< moving-diagram >}}
{
  "title": "Retries multiply down a chain",
  "subtitle": "users is down; every caller retries once",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 150,
  "boxes": {
    "orders":   [60, 150, 200, 230, "orders"],
    "payments": [330, 150, 470, 230, "payments"],
    "users":    [600, 150, 740, 230, "users", "down"]
  },
  "wires": [
    [[200,175],[330,175]],
    [[330,205],[200,205]],
    [[470,175],[600,175]],
    [[600,205],[470,205]]
  ],
  "moves": [
    { "start": 5,   "end": 20,  "path": [[200,175],[330,175]], "color": "primary", "label": "try 1" },
    { "start": 22,  "end": 34,  "path": [[470,175],[600,175]], "color": "primary", "label": "call" },
    { "start": 36,  "end": 46,  "path": [[600,205],[470,205]], "color": "secondary", "label": "timeout" },
    { "start": 48,  "end": 60,  "path": [[470,175],[600,175]], "color": "primary", "label": "retry" },
    { "start": 62,  "end": 72,  "path": [[600,205],[470,205]], "color": "secondary", "label": "timeout" },
    { "start": 74,  "end": 88,  "path": [[330,205],[200,205]], "color": "secondary", "label": "error" },
    { "start": 92,  "end": 106, "path": [[200,175],[330,175]], "color": "primary", "label": "try 2" },
    { "start": 108, "end": 120, "path": [[470,175],[600,175]], "color": "primary", "label": "call" },
    { "start": 122, "end": 132, "path": [[600,205],[470,205]], "color": "secondary", "label": "timeout" },
    { "start": 134, "end": 146, "path": [[470,175],[600,175]], "color": "primary", "label": "retry" },
    { "start": 148, "end": 158, "path": [[600,205],[470,205]], "color": "secondary", "label": "timeout" },
    { "start": 160, "end": 174, "path": [[330,205],[200,205]], "color": "secondary", "label": "error" }
  ],
  "tags": [
    { "start": 0,   "end": 34,  "x": 670, "y": 120, "text": "calls to users: 0", "color": "secondary" },
    { "start": 34,  "end": 60,  "x": 670, "y": 120, "text": "calls to users: 1", "color": "secondary" },
    { "start": 60,  "end": 120, "x": 670, "y": 120, "text": "calls to users: 2", "color": "secondary" },
    { "start": 120, "end": 146, "x": 670, "y": 120, "text": "calls to users: 3", "color": "secondary" },
    { "start": 146, "end": 250, "x": 670, "y": 120, "text": "calls to users: 4", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 90,  "text": "users is down, so payments retries once", "color": "primary" },
    { "start": 90,  "end": 176, "text": "orders retries too, and the whole subtree runs again", "color": "secondary" },
    { "start": 176, "end": 999, "text": "2 layers, 1 retry each: (1+1)^2 = 4 calls to users", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 2: With users down, a retry at each layer repeats everything below it, so the calls reaching users double with every layer.*

The usual fix is to retry at one layer only, often the edge. A retry budget per client and a circuit breaker help too, so callers stop hitting a service that's already down.

## The Prime Video case

In March 2023 the Prime Video tech blog described one service, the tool that monitors stream quality. Its first version ran on AWS Step Functions and Lambda, and passed video frames between steps through S3. Step Functions bills per state transition, and every frame meant S3 calls, so both costs grew with load. The team moved everything into one process on Amazon ECS, passed frames in memory, and cut infrastructure cost by over 90%. To grow, they ran several copies of that process. That's scaling out a monolith.[^cockcroft]

The lesson is narrow. When parts hand each other a lot of data, moving the data can cost more than processing it. It isn't a verdict on microservices in general.

## When splitting is the right call

The strongest traffic argument for services is that you scale only the busy part. For a typical web app the idle modules cost each copy some memory, not CPU, so it only wins when the busy part needs different hardware.

**Very different resources.** Video transcoding wants CPU or a GPU and can wait in a queue. Checkout wants low latency and must stay up. In one process you size every copy for the worse of the two, and a transcoding spike slows checkout. Split, each scales and fails on its own.

**Teams blocking each other.** With a few dozen engineers in one codebase you get long merge queues, release trains, and one team's broken test holding up everyone's deploy. Separate services with separate pipelines fix exactly that.

A middle step is the modular monolith: one deployable with enforced boundaries inside it. Shopify has written about doing this with its large Rails codebase.[^shopify] You get most of the ownership with none of the hops, and the boundary is already drawn if a component later needs to move out.

## When it's the wrong call

Splitting backfires when the team is small. Every service needs a pipeline, dashboards, alerts, tracing and someone on call, and with five engineers that work lands on the people meant to ship features. It also backfires when domain boundaries aren't clear yet, or when services share one database. Then two services must change and deploy together for every feature. The [microservices fundamentals](../../architecture/microservices-fundamentals.md) note covers why database-per-service keeps deploys independent. Get it wrong and you've built a distributed monolith: the network costs without the independence.

## What to measure

Before splitting, find out which scale hurts. For traffic, check CPU and memory per copy and the database, which is usually the real limit. For teams, check deploy frequency, merge-to-production time, and how often one team's change blocks another's release.

After splitting, track hops on the critical path, p99 per hop, retry rate per client and pages per on-call engineer. If those climb and deploy frequency doesn't, the split cost more than it gave back.

## References

**Case studies**
- [Reduce costs by 90% by moving from microservices to monolith](https://devclass.com/2023/05/05/reduce-costs-by-90-by-moving-from-microservices-to-monolith-amazon-internal-case-study-raises-eyebrows/), DevClass, May 2023. Coverage of the Prime Video post. The original on primevideotech.com now redirects.
- [Prime Video monolith debate](https://thestack.technology/prime-video-monolith-architecture-debate-bad-takes-adrian-cockcroft), Adrian Cockcroft in The Stack. The counter-reading of the same case.
- [Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), Kirsten Westeinde, Shopify Engineering, 2019.

**Essays**
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html), Martin Fowler.
- [Microservices](https://martinfowler.com/articles/microservices.html), James Lewis and Martin Fowler, 2014.

[^hop]: A rough range, not a measurement. Payload size, serialization, connection reuse and service-mesh sidecars all move it.
[^avail]: 0.999⁴ ≈ 0.996, so the failure rate goes from 0.1% to about 0.4%.
[^cockcroft]: Adrian Cockcroft reads it differently: the team reused most of its code as one long-running service, scaled horizontally on ECS, which he calls the normal next step after a serverless prototype. Both readings agree the savings came from passing frames in memory.
[^shopify]: In the 2019 post, Shopify tracked boundary violations with a tool (Wedge) rather than blocking them outright. Strict enforcement was still a goal.
