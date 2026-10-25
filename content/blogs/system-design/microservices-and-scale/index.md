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
mermaid: true
---

"Scale" covers two different problems. Traffic scale is handling more requests per second. Team scale is letting more engineers ship without stepping on each other. A microservice is a small service that deploys on its own and talks to the other services over the network, and splitting into microservices mostly helps team scale. For traffic, a stateless monolith already scales out: run ten copies behind a load balancer. Splitting it turns function calls into network calls, and each one adds latency and one more place to fail. A request that crosses four services instead of one pays three extra hops, multiplies four availability numbers together, and can turn one retry policy into dozens of calls when something deep in the chain goes down. Split a service out when one part needs very different resources, or when teams keep blocking each other's deploys. Otherwise, scale the monolith first.

## Two kinds of scale

- **Traffic scale**: handling more requests per second.
- **Team scale**: letting more engineers ship without stepping on each other. That means independent deploys and fewer merge and release conflicts.

A **monolith** is one deployable application where modules call each other in-process, through plain function calls. A **microservice** deploys on its own and reaches the others over the network.

The two definitions already point at the answer. Nothing about deploying separately gives a request more CPU. What it gives you is the freedom for the payments team to release on Tuesday without waiting for the search team's fix.

## The same request, two ways

Take an order that touches three modules: orders, payments and users. In the monolith, the client makes one network call. Orders calls payments, payments calls users, and both of those are function calls that cost nanoseconds and can't time out. Split the same code into three services and every arrow becomes a network hop with its own timeout, its own retry policy and its own way to fail.

{{< mermaid >}}
sequenceDiagram
  participant C as Client
  participant O as orders
  participant P as payments
  participant U as users
  C->>O: POST /orders
  O->>P: charge (network hop)
  P-xU: get user (times out)
  P->>U: get user (retry)
  U-->>P: user
  P-->>O: charged
  O-->>C: 201 Created
  Note over O,U: In the monolith these three are one process and the middle calls are function calls
{{< /mermaid >}}

The animation runs both versions side by side. The top row finishes after one network call. The bottom row needs three hops plus a retry, and it finishes much later.

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

## Why splitting doesn't add capacity

Capacity comes from machines. A stateless monolith keeps no session in its own memory, so you can put as many copies behind a load balancer as the database allows. That's plain [horizontal scaling](../vertical-vs-horizontal-scaling/), and it works the same whether the code inside is one module or forty. Ten copies of the monolith give you ten copies of orders, payments and users.

Splitting moves the same work onto more boxes and adds work on top: serializing the request, sending it, parsing it on the other side, and the same again for the response. Inside one data center a hop costs somewhere around a millisecond or a few, plus the tail. The [Latency vs Throughput](../latency-vs-throughput/) note explains why that tail is what users feel: a request that crosses five services waits on the slowest of five p99s. New connections cost round trips too, as the [URL to first byte](../how-a-url-becomes-a-webpage/) note shows, so services that skip connection pooling pay for TCP and TLS over and over.

Failure multiplies the same way. If each service is up 99.9% of the time and a request needs four of them in a row, the request succeeds 99.6% of the time. That's roughly four times the downtime of one process.

Retries are worse. Say each caller retries a failed call twice, which sounds sensible. When the last service in a chain of four goes down, the third service tries it three times, and each failure goes back up the chain. The second service retries the third three times, and the first does the same. The dead service ends up taking 3 × 3 × 3 = 27 calls for one user click, right when it's trying to recover.

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

The usual fixes are to retry at one layer only (often the edge), put a retry budget on each client, and add a circuit breaker so callers stop knocking on a service that's already down.

## Do the sums

Change the number of services a request passes through and see what the hops cost. Set it to 1 for the monolith.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "One request through the chain",
      "inputs": [
        { "id": "services", "label": "Services the request passes through, in order", "default": 4, "step": 1 },
        { "id": "workMs", "label": "Total work across all of them", "default": 20, "step": 5, "unit": "ms" },
        { "id": "hopMs", "label": "Cost of one internal network call", "default": 5, "step": 1, "unit": "ms" }
      ],
      "outputs": [
        { "id": "hops", "label": "Network hops between services", "formula": "Math.max(0, Math.floor(services) - 1)", "format": "number" },
        { "id": "monoMs", "label": "Backend time as one process (ms)", "formula": "Math.max(0, workMs)", "format": "number" },
        { "id": "splitMs", "label": "Backend time split into services (ms)", "formula": "Math.max(0, workMs) + hops * Math.max(0, hopMs)", "format": "number" },
        { "id": "hopShare", "label": "Share of that time spent on hops (%)", "formula": "splitMs > 0 ? hops * Math.max(0, hopMs) / splitMs * 100 : 0", "format": "number" }
      ]
    },
    {
      "title": "When something fails",
      "inputs": [
        { "id": "availPct", "label": "Uptime of each service", "default": 99.9, "step": 0.1, "unit": "%" },
        { "id": "retries", "label": "Retries per failed call, at every layer", "default": 2, "step": 1 }
      ],
      "outputs": [
        { "id": "monoAvail", "label": "Request success, one process (%)", "formula": "Math.min(Math.max(availPct, 0), 100)", "format": "number" },
        { "id": "splitAvail", "label": "Request success, split (%)", "formula": "Math.pow(monoAvail / 100, hops + 1) * 100", "format": "number" },
        { "id": "monoDown", "label": "Hours a month failing, one process", "formula": "(100 - monoAvail) / 100 * 730", "format": "number" },
        { "id": "splitDown", "label": "Hours a month failing, split", "formula": "(100 - splitAvail) / 100 * 730", "format": "number" },
        { "id": "amplify", "label": "Calls reaching the last service when it's down", "formula": "Math.pow(Math.max(0, Math.floor(retries)) + 1, hops)", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

The model assumes the services are called one after another (no parallel fan-out), every hop costs the same, services fail independently with the same uptime, and every layer retries the full count before giving up. The client's own retries are left out because both designs have them. With the defaults: 3 hops, 20 ms as one process against 35 ms split (43% of it on hops), 99.9% success against 99.6%, which is 0.73 hours a month of failures against 2.92. If the last service dies, 3³ = 27 calls reach it.

## The Prime Video case

In March 2023 the Prime Video tech blog described one service: the tool that monitors the audio and video quality of streams. It was one monitoring service, and the post says nothing about the rest of Prime Video's architecture.

The first version was distributed. AWS Step Functions orchestrated the steps, Lambda functions ran the checks, and a component split the video into frames and stored them in S3 for the detectors to download. Two costs grew with load. Step Functions charges per state transition, and the service made several transitions for every second of every stream, so it also ran into account limits. Passing frames through S3 meant a large number of S3 calls, which cost money for every frame.

The team moved all the components into one process, running on Amazon ECS, so frames were passed in memory. Infrastructure cost dropped by over 90%. To grow past one machine they ran several copies of that process, each handling part of the work. That's scaling out a monolith.

The lesson is narrow. When the parts hand each other a lot of data, moving the data between them can cost more than processing it. It's no verdict against serverless or against microservices in general.

## When splitting is the right call

**Very different resources.** Video transcoding wants lots of CPU or a GPU and can wait in a queue. Checkout wants low latency and has to be up. Running them in one process means you size every copy for the worse of the two, and a transcoding spike can slow checkout. Pulling transcoding out lets each one scale and fail on its own.

**Teams blocking each other.** With a few dozen engineers in one codebase, the pain shows up as a long merge queue, release trains everyone must board, and one team's broken test holding up everyone else's deploy. Separate services with separate pipelines fix exactly that. This is what microservices are best at.

There's a middle step. A modular monolith keeps one deployable but enforces boundaries between components inside it. Shopify has written publicly about doing this with its large Rails codebase. You get most of the code ownership and none of the network hops, and if one component later needs to move out, its boundary is already drawn.

## When it's the wrong call

Splitting backfires when the team is small. Every new service needs a pipeline, dashboards, alerts, tracing and somebody on call at 3am, and with four or five engineers that work lands on the same people who were supposed to ship features. It also backfires when the domain boundaries aren't clear yet. Cut in the wrong place and two services have to change and deploy together for every feature. Sharing one database across services has the same effect, and the [microservices fundamentals](../../architecture/microservices-fundamentals.md) note explains why database-per-service is the rule that keeps deploys independent. Get that wrong and you've built a distributed monolith: all the network costs of microservices, and none of the independence.

## What to measure

Before splitting, check which kind of scale hurts. For traffic, look at CPU and memory per copy and at the database, which is usually the real limit. For team scale, measure deploy frequency, time from merge to production, how long changes sit in the merge queue, and how often one team's change blocks another's release.

After splitting, track hops on the critical path of your main requests, p99 latency per hop, retry rate per client and pages per on-call engineer. If those climb and deploy frequency doesn't, the split cost more than it gave back.
