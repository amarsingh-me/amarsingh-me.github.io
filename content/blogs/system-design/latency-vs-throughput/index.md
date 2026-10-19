---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-20T00:00:00+08:00
title: Latency vs Throughput
tags: [system-design, performance, distributed-systems]
categories: [System Design]
mermaid: true
---

Latency is how long one request takes. Throughput is how many requests you finish per second. Latency comes in two kinds:

- **Network latency**: the time data takes to travel one way, from point A to point B.
- **Request latency**: the full round trip (there and back) plus the time the server spends processing the request.

In practice, network latency is only part of the wait. It's the travel time, and you can't do much about it beyond moving servers closer to users. Request latency adds the trip back and everything your server does in between, including time a request spends waiting in a queue. That total is what users feel, so when this series says "latency" it means request latency.

Latency and throughput move independently until the system gets busy. Near max throughput, requests start waiting in queues and latency climbs fast: at 50% utilization a request spends about twice its service time in the system, and at 90% it spends about ten times. Batching and more servers raise throughput. Caching cuts latency. Neither fixes the other, and the way to see trouble coming is to watch p99 and keep headroom, not to watch the average.

## Two kinds of latency

Take the highway picture from the LinkedIn post. Latency is how long one car takes to get from A to B. For request latency it's the drive there, the stop, and the drive back.

**Network latency** has a hard floor set by physics. Light in fiber covers roughly 200 km per millisecond, so New York to London (about 5,600 km) costs at least 28 ms one way before any router, TLS handshake or retransmit gets involved. No code change makes that shorter. You can only move the server closer to the user.

**Request latency** is everything the user waits for: the trip out, the time your server spends on the request, and the trip back. Server time is the part you control, and it includes waiting. Time spent sitting in a thread pool queue or a connection pool counts the same as time spent doing work.

{{< moving-diagram >}}
{
  "title": "Latency",
  "subtitle": "One full round trip: 50 ms there, 20 ms processing, 50 ms back",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "client": [60, 140, 240, 200, "Client"],
    "server": [560, 140, 740, 200, "Server"]
  },
  "wires": [
    [[240,160],[320,80],[480,80],[560,160]],
    [[560,180],[480,260],[320,260],[240,180]]
  ],
  "moves": [
    { "start": 8,  "end": 50,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "request" },
    { "start": 65, "end": 107, "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "response" }
  ],
  "captions": [
    { "start": 0,   "end": 50,  "text": "0 ms: the client sends one request", "color": "primary" },
    { "start": 50,  "end": 65,  "text": "50 ms: it arrives (network latency, one way)", "color": "primary" },
    { "start": 65,  "end": 107, "text": "70 ms: the server is done, the response heads back", "color": "secondary" },
    { "start": 107, "end": 999, "text": "120 ms: request latency = one full round trip", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## Throughput is a rate

Throughput counts finished requests per unit of time. On the highway, it's the number of cars passing the exit per hour. It says nothing about how long any one car took.

That's why a server can have 120 ms latency and still do far more than 8 requests per second (1,000 / 120). It doesn't wait for one reply before sending the next request. Several are in flight at once, and throughput depends on how many it can keep in flight, not on how long each one takes.

{{< moving-diagram >}}
{
  "title": "Throughput",
  "subtitle": "Requests completed per second",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "client": [60, 140, 240, 200, "Client"],
    "server": [560, 140, 740, 200, "Server"]
  },
  "wires": [
    [[240,160],[320,80],[480,80],[560,160]],
    [[560,180],[480,260],[320,260],[240,180]]
  ],
  "moves": [
    { "start": 5,   "end": 14,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 1" },
    { "start": 15,  "end": 24,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 2" },
    { "start": 25,  "end": 34,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 3" },
    { "start": 35,  "end": 44,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 4" },
    { "start": 45,  "end": 54,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 5" },
    { "start": 55,  "end": 64,  "path": [[240,160],[320,80],[480,80],[560,160]], "color": "primary", "label": "req 6" },
    { "start": 70,  "end": 79,  "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 1" },
    { "start": 80,  "end": 89,  "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 2" },
    { "start": 90,  "end": 99,  "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 3" },
    { "start": 100, "end": 109, "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 4" },
    { "start": 110, "end": 119, "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 5" },
    { "start": 120, "end": 129, "path": [[560,180],[480,260],[320,260],[240,180]], "color": "secondary", "label": "done 6" }
  ],
  "captions": [
    { "start": 0,   "end": 66,  "text": "six requests go out back to back, without waiting for replies", "color": "primary" },
    { "start": 66,  "end": 130, "text": "six are in flight; responses come back in order", "color": "secondary" },
    { "start": 130, "end": 999, "text": "6 completed in 1.0 s = throughput of 6 requests/second", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

One law ties the two together. **Little's Law** says the average number of requests in the system equals arrival rate times average time in the system: L = λ × W. At 500 requests per second and 200 ms each, you have 100 requests in flight on average. If your service has 50 worker threads, that math says you're already queueing. It's a quick sanity check for any pool size.

## Why latency spikes near capacity

Adding lanes to the highway moves more cars per hour. Your own trip isn't any shorter. And at rush hour, when the road hits capacity, cars queue and everyone's trip gets slower. Servers behave the same way.

When requests arrive at random (they always do), a server at 70% busy will still sometimes get five requests in the same instant. Four of them wait. The simplest queueing model (M/M/1: one worker, random arrivals, random service times) puts the average time in the system at:

```
response time = service time / (1 - utilization)
```

At 50% utilization that's 2× the service time. At 80% it's 5×, at 90% it's 10×, and at 99% it's 100×. The curve is flat for a long time and then goes nearly vertical. That's the trap in the post: near max throughput, latency spikes. Dashboards that only show throughput look healthy right up to the moment users start timing out.

{{< mermaid >}}
sequenceDiagram
  participant C as Client
  participant Q as Queue
  participant W as Worker
  C->>Q: request (quiet hour)
  Q->>W: picked up at once
  W-->>C: response after 20 ms
  C->>Q: request (rush hour)
  Note over Q: waits behind the requests already queued
  Q->>W: picked up much later
  W-->>C: response after 200 ms (same 20 ms of work)
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Rush hour",
  "subtitle": "Same work, longer wait: the queue adds the latency",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 220,
  "boxes": {
    "client": [30, 140, 190, 200, "Client"],
    "queue":  [310, 140, 470, 200, "Queue"],
    "worker": [590, 140, 770, 200, "Worker"]
  },
  "wires": [
    [[190,170],[590,170]],
    [[680,200],[680,270],[110,270],[110,200]]
  ],
  "moves": [
    { "start": 8,   "end": 58,  "path": [[190,170],[590,170],[680,200],[680,270],[110,270],[110,200]], "color": "primary", "label": "quiet: 20 ms" },
    { "start": 72,  "end": 80,  "path": [[190,170],[320,170]], "color": "secondary", "label": "car" },
    { "start": 82,  "end": 90,  "path": [[190,170],[320,170]], "color": "secondary", "label": "car" },
    { "start": 92,  "end": 100, "path": [[190,170],[320,170]], "color": "secondary", "label": "car" },
    { "start": 104, "end": 200, "path": [[190,170],[320,170],[460,150],[320,190],[460,150],[320,190],[460,150],[320,190],[460,170],[590,170],[680,200],[680,270],[110,270],[110,200]], "color": "primary", "label": "rush: 200 ms" }
  ],
  "captions": [
    { "start": 0,   "end": 62,  "text": "quiet hour: the queue is empty, so latency = service time", "color": "primary" },
    { "start": 62,  "end": 104, "text": "rush hour: requests arrive faster than the worker clears them", "color": "secondary" },
    { "start": 104, "end": 170, "text": "the next request waits in the queue behind them", "color": "secondary" },
    { "start": 170, "end": 999, "text": "the work still takes 20 ms; the extra time was all waiting", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

Real systems with a shared queue and many workers do better than one worker on its own, but the curve has the same shape. Play with it below. The model treats each worker as its own M/M/1 queue, which is pessimistic but close enough to show where the knee is. A dash means the arrival rate is above capacity and the queue grows without limit.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Your service",
      "inputs": [
        { "id": "serviceMs", "label": "Service time per request", "default": 50, "step": 5, "unit": "ms" },
        { "id": "workers", "label": "Workers (threads x servers)", "default": 8, "step": 1 },
        { "id": "arrivalRps", "label": "Arrival rate", "default": 120, "step": 10, "unit": "req/s" }
      ],
      "outputs": [
        { "id": "capacityRps", "label": "Max throughput (req/s)", "formula": "workers * 1000 / serviceMs", "format": "number" },
        { "id": "utilPct", "label": "Utilization (%)", "formula": "arrivalRps / capacityRps * 100", "format": "number" }
      ]
    },
    {
      "title": "What users feel",
      "outputs": [
        { "id": "avgMs", "label": "Average request latency (ms)", "formula": "utilPct < 100 ? serviceMs / (1 - utilPct / 100) : NaN", "format": "number" },
        { "id": "waitMs", "label": "Of which waiting in queue (ms)", "formula": "avgMs - serviceMs", "format": "number" },
        { "id": "p99Ms", "label": "p99 latency (ms)", "formula": "avgMs * Math.log(100)", "format": "number" },
        { "id": "inFlight", "label": "Requests in flight (Little's Law)", "formula": "arrivalRps * avgMs / 1000", "format": "number" }
      ]
    },
    {
      "title": "Fan-out and the tail",
      "inputs": [
        { "id": "slowPct", "label": "Backend calls that are slow", "default": 1, "step": 0.5, "unit": "%" },
        { "id": "callsPerPage", "label": "Backend calls per page", "default": 20, "step": 1 }
      ],
      "outputs": [
        { "id": "pageSlowPct", "label": "Pages that hit a slow call (%)", "formula": "(1 - Math.pow(1 - slowPct / 100, callsPerPage)) * 100", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

With the defaults, a 50 ms endpoint averages 200 ms at 75% utilization. Push arrivals from 120 to 150 req/s, only 25% more traffic, and the average goes to 800 ms. This is the 50 ms API that falls over at 1,000 users. Each request was always fast. The server just ran out of room to absorb bursts.

## Watch p99, not the average

The average hides the requests people complain about. If 1 in 100 backend calls is slow and a page makes 20 of them, the page hits at least one slow call 18% of the time, almost 1 in 5 (the calculator above does that math). At 100 calls per page it's 63%. Google's "The Tail at Scale" paper (Dean and Barroso, 2013) is the standard reference here, and it's why big systems send a backup request to a second replica when the first is slower than its p95.

Two measurement mistakes hide the tail even when you do look at percentiles:

- **Averaging percentiles.** The mean of ten servers' p99 values is not the fleet's p99. Merge histograms (HdrHistogram, Prometheus histogram buckets) and compute the percentile from the merged data.
- **Coordinated omission.** A load tester that waits for each response before sending the next request slows down exactly when the server stalls, so it records fewer slow samples than a real user would hit. Use a tool that sends at a fixed rate, like wrk2 or k6's constant arrival rate mode.

And leave headroom. If the curve goes vertical past about 70–80% utilization, plan capacity so a normal peak lands below that, not at 95%.

## What each lever does, and when it's the wrong one

**Batching** sends many messages in one network call. A [Kafka producer](../../kafka/apache-kafka-concepts/index.md) with `linger.ms=10` and a decent `batch.size` pays the network and request overhead once per batch instead of once per record, so throughput goes up a lot. Each message now waits up to 10 ms for the batch to fill. That's a fine trade for a log pipeline and a bad one for an order-placement call that a user is staring at.

**Caching and CDNs** answer from memory or from a server near the user. Latency drops, and the backend does less work, so throughput improves too. The failure modes are specific. A cache miss is slower than having no cache, since you pay the cache lookup and then the database. A cold cache after a deploy or a mass expiry sends every request to the database at once (the thundering herd). And a cache with a 99% hit rate still leaves the 1% on the slow path, which is exactly where your p99 lives.

**Horizontal scaling** adds servers behind a load balancer: more lanes, more throughput, and a single request is no faster. It's the wrong lever when the bottleneck is something the servers share. Ten app servers hammering one Postgres primary, or fighting over one row lock, give you ten times the contention and the same database ceiling. It also doesn't help if one request is slow because of its own work, like a 2-second report query.

**Bounding queues** is the lever people forget. An unbounded queue turns overload into unbounded latency: every request eventually succeeds, minutes too late. A [bounded queue with a rejection policy](../../java/concurrency/executors-and-thread-pools.md) fails some requests fast so the rest stay quick. Most users prefer a fast error and a retry to a 40-second spinner.

## Know which one your users feel

A trading app lives on latency. A slow order can fill at a worse price, and no amount of throughput makes up for it. A data pipeline lives on throughput: nobody waits on one record, but the nightly job has to finish before the morning reports run. Most services sit between the two, so measure both. Track throughput and utilization to know how close you are to the knee, and track p99 latency to see what the slowest users get. If you're sizing a new system, start with [back-of-the-envelope estimation](../back-of-the-envelope-estimation.md) to get the peak request rate, then check where that lands on the curve above.
