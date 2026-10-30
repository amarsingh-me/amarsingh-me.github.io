---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-30T00:00:00+08:00
title: "5 Latency Numbers Every Engineer Should Know"
tags: [system-design, performance, distributed-systems]
categories: [System Design]
mermaid: true
---

An endpoint reads 50 keys from Redis, one `GET` at a time, and spends 25 ms doing it. Redis found each key in a few microseconds. The other 99% of the time went to the network: about half a millisecond per round trip inside a datacenter, paid 50 times in a row. **Count the round trips before you count anything else, because a network round trip costs thousands of RAM reads.** I call this the **round-trip tax**. You don't need exact digits to see it coming. Five rough numbers are enough: memory at ~100 ns, SSD at ~100 µs, a datacenter round trip at ~0.5 ms, a disk seek at ~10 ms, and California to Europe and back at ~150 ms. 

## The terms

- **Latency**: the time from asking to getting the answer for one operation. On a network, that means the full round trip.
- **RAM read**: ~100 ns.
- **SSD random read**: ~100 µs. Modern NVMe drives can be faster; this post uses ~100 µs.
- **Round trip inside a datacenter**: ~0.5 ms.
- **Hard disk seek**: ~10 ms, on a spinning disk.
- **California to Europe and back**: ~150 ms.
- **The round-trip tax**: the waiting you pay for every network call made one after another. It grows with the number of sequential trips, not with how much work the server does.

The numbers come from the list Jeff Dean made famous, which Peter Norvig also printed in "Teach Yourself Programming in Ten Years". His table has main memory at 100 ns, a disk seek at 8 ms and a packet from the US to Europe and back at 150 ms.

## A world where a RAM read takes 1 second

Nanoseconds and milliseconds are both "fast" to a person, which is why the gap between them is easy to forget. Imagine a world where a RAM read takes 1 second. In that world, an SSD read takes 17 minutes, and a datacenter round trip takes almost an hour and a half (about 80 minutes). A disk seek eats a whole day, and California to Europe and back takes 17 days.

{{< moving-diagram >}}
{
  "title": "Latency numbers",
  "subtitle": "Log scale. Right side: the same wait if a RAM read took 1 second",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 205,
  "boxes": {
    "l1": [20, 20, 210, 64, "RAM read", "~100 ns"],
    "l2": [20, 84, 210, 128, "SSD random read", "~100 µs"],
    "l3": [20, 148, 210, 192, "Datacenter round trip", "~0.5 ms"],
    "l4": [20, 212, 210, 256, "Hard disk seek", "~10 ms"],
    "l5": [20, 276, 210, 320, "California ↔ Europe", "~150 ms"],
    "b1": [230, 30, 238, 54, ""],
    "b2": [230, 94, 238, 118, ""],
    "b3": [230, 158, 238, 182, ""],
    "b4": [230, 222, 238, 246, ""],
    "b5": [230, 286, 238, 310, ""]
  },
  "wires": [],
  "moves": [
    { "start": 12,  "end": 37,  "path": [[230,42],[266,42]],   "color": "primary" },
    { "start": 47,  "end": 72,  "path": [[230,106],[501,106]], "color": "primary" },
    { "start": 82,  "end": 107, "path": [[230,170],[556,170]], "color": "primary" },
    { "start": 117, "end": 142, "path": [[230,234],[658,234]], "color": "primary" },
    { "start": 152, "end": 177, "path": [[230,298],[750,298]], "color": "secondary" }
  ],
  "resize": [
    { "box": "b1", "start": 12,  "end": 37,  "to": [230, 30, 266, 54] },
    { "box": "b2", "start": 47,  "end": 72,  "to": [230, 94, 501, 118] },
    { "box": "b3", "start": 82,  "end": 107, "to": [230, 158, 556, 182] },
    { "box": "b4", "start": 117, "end": 142, "to": [230, 222, 658, 246] },
    { "box": "b5", "start": 152, "end": 177, "to": [230, 286, 750, 310] },
    { "box": "b1", "start": 232, "end": 246, "to": [230, 30, 238, 54] },
    { "box": "b2", "start": 232, "end": 246, "to": [230, 94, 238, 118] },
    { "box": "b3", "start": 232, "end": 246, "to": [230, 158, 238, 182] },
    { "box": "b4", "start": 232, "end": 246, "to": [230, 222, 238, 246] },
    { "box": "b5", "start": 232, "end": 246, "to": [230, 286, 238, 310] }
  ],
  "tags": [
    { "text": "1 s",     "x": 290, "y": 46,  "start": 37,  "end": 232, "color": "primary" },
    { "text": "17 min",  "x": 470, "y": 110, "start": 72,  "end": 232, "color": "primary" },
    { "text": "1.4 h",   "x": 525, "y": 174, "start": 107, "end": 232, "color": "primary" },
    { "text": "1 day",   "x": 625, "y": 238, "start": 142, "end": 232, "color": "primary" },
    { "text": "17 days", "x": 715, "y": 302, "start": 177, "end": 232, "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 47,  "text": "RAM read: ~100 ns, call it 1 second", "color": "primary" },
    { "start": 47,  "end": 82,  "text": "SSD random read: 1,000× slower, 17 minutes", "color": "primary" },
    { "start": 82,  "end": 117, "text": "one datacenter round trip: 5,000×, about 80 minutes", "color": "primary" },
    { "start": 117, "end": 152, "text": "disk seek: 100,000×, a whole day", "color": "primary" },
    { "start": 152, "end": 185, "text": "California to Europe and back: 17 days", "color": "secondary" },
    { "start": 185, "end": 999, "text": "RAM vs Europe and back: ~1,000,000×", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 1: Each bar is one tier on a log scale. Watch the jump from the first bar to the third: a datacenter round trip is 5,000 RAM reads.*

The row to remember is the third one. It's the one people forget, because "Redis is in memory" sounds like the first row. Redis keeps its data in RAM, but your app doesn't. Every `GET` is a request over the network, and the network sets the price.

The last row has a floor that no code can lower. Light in fibre covers about 200 km per millisecond, so a 9,000 km cable path costs about 90 ms there and back before any router touches the packet.[^1] Serving users from a nearby region or a CDN is the only fix, which the [URL to webpage](../how-a-url-becomes-a-webpage/) note walks through hop by hop.

## Where the 25 ms went

Each `GET` is one round trip of ~0.5 ms plus a few microseconds of work inside Redis. Fifty of them in sequence cost 50 × 0.5 ms = 25 ms of waiting and about 0.25 ms of work. In the world where a RAM read takes 1 second, the endpoint runs 50 of those 80-minute errands one after another.

{{< moving-diagram >}}
{
  "title": "The round-trip tax",
  "subtitle": "Same 50 keys: one GET at a time, then one MGET",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 300,
  "posterFrame": 210,
  "boxes": {
    "app":   [40, 150, 200, 230, "App", "endpoint"],
    "redis": [600, 150, 760, 230, "Redis", "~5 µs per key"]
  },
  "wires": [
    [[200,170],[280,90],[520,90],[600,170]],
    [[600,210],[520,290],[280,290],[200,210]]
  ],
  "moves": [
    { "start": 10,  "end": 25,  "path": [[200,170],[280,90],[520,90],[600,170]], "color": "primary", "label": "GET k1" },
    { "start": 27,  "end": 42,  "path": [[600,210],[520,290],[280,290],[200,210]], "color": "primary", "label": "v1" },
    { "start": 45,  "end": 60,  "path": [[200,170],[280,90],[520,90],[600,170]], "color": "primary", "label": "GET k2" },
    { "start": 62,  "end": 77,  "path": [[600,210],[520,290],[280,290],[200,210]], "color": "primary", "label": "v2" },
    { "start": 80,  "end": 95,  "path": [[200,170],[280,90],[520,90],[600,170]], "color": "primary", "label": "GET k3" },
    { "start": 97,  "end": 112, "path": [[600,210],[520,290],[280,290],[200,210]], "color": "primary", "label": "v3" },
    { "start": 115, "end": 130, "path": [[200,170],[280,90],[520,90],[600,170]], "color": "primary", "label": "GET k4" },
    { "start": 132, "end": 147, "path": [[600,210],[520,290],[280,290],[200,210]], "color": "primary", "label": "v4" },
    { "start": 180, "end": 200, "path": [[200,170],[280,90],[520,90],[600,170]], "color": "secondary", "label": "MGET k1..k50" },
    { "start": 203, "end": 223, "path": [[600,210],[520,290],[280,290],[200,210]], "color": "secondary", "label": "50 values" }
  ],
  "captions": [
    { "start": 0,   "end": 45,  "text": "trip 1: 0.5 ms on the wire, ~5 µs in Redis", "color": "primary" },
    { "start": 45,  "end": 115, "text": "each GET waits for the last reply before it goes", "color": "primary" },
    { "start": 115, "end": 175, "text": "...46 more trips: 50 × 0.5 ms = 25 ms waiting", "color": "primary" },
    { "start": 175, "end": 225, "text": "MGET: all 50 keys in one request", "color": "secondary" },
    { "start": 225, "end": 999, "text": "one round trip ≈ 0.5 ms instead of 25 ms", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 2: The dot spends almost all its time on the wires, not inside Redis. MGET makes the same 50 lookups in one trip.*

The same shape shows up outside Redis. An ORM loads 50 orders, then runs one query per order to fetch its customer. That's the N+1 query problem: 51 database round trips where a `JOIN` or one `WHERE id IN (...)` query would make one. Chatty microservices do it too. Splitting a service turns an in-process call that took nanoseconds into a 0.5 ms round trip, as the [microservices and scale](../microservices-and-scale/) note explains. A request that hops through four services, each calling the next in sequence, pays the round-trip tax at every hop.

## Four ways to pay less

#### Batch
One `MGET` or one pipeline is one trip, while 50 `GET`s are 50. The Redis pipelining docs make the same point with a slow link: at a 250 ms round trip, a server that handles 100k requests per second still lets one client finish only four requests per second. Pipelining also cuts the `read()` and `write()` syscalls Redis has to make, so it raises server throughput as well.

#### Run them in parallel when you can't batch
If the keys live behind different services, send the calls at once and wait for the slowest instead of the sum. Ten calls in flight turn 50 trips into five waves, about 2.5 ms.

#### Keep hot data that can be slightly stale in local memory
A read from the process's own heap is a RAM read, about 5,000 times cheaper than a datacenter round trip. Config, feature flags and product catalogues are the usual candidates.

#### Serve users from nearby
 For the 150 ms row, only distance helps. A CDN or a regional deployment moves the server closer. Faster code can't move the light.

The first two fixes change how many trips happen one after another. Here are three ways to ask for the same 50 keys.

{{< mermaid >}}
sequenceDiagram
  participant A as App
  participant R as Redis
  loop 50 times, one after another
    A->>R: GET key
    R-->>A: value (0.5 ms trip)
  end
  A->>R: MGET key1 ... key50
  R-->>A: 50 values (one 0.5 ms trip)
  par 50 calls at once
    A->>R: GET key1
  and
    A->>R: GET key50
  end
  R-->>A: replies (wait for the slowest)
{{< /mermaid >}}

*Figure 3: The loop pays the round-trip tax 50 times, MGET pays it once, and parallel calls pay it once but wait on the slowest reply.*

Put your own numbers into the calculator. Server time per key is a guess you should replace with a measurement.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "The calls",
      "inputs": [
        { "id": "keys", "label": "Keys to read", "default": 50, "step": 1 },
        { "id": "rttMs", "label": "Round trip", "default": 0.5, "step": 0.1, "unit": "ms" },
        { "id": "workUs", "label": "Server time per key", "default": 5, "step": 1, "unit": "µs" },
        { "id": "conns", "label": "Calls in flight at once (parallel case)", "default": 10, "step": 1 }
      ]
    },
    {
      "title": "Time spent",
      "outputs": [
        { "id": "seqMs", "label": "One GET at a time (ms)", "formula": "keys * (rttMs + workUs / 1000)", "format": "number" },
        { "id": "batchMs", "label": "One MGET or pipeline (ms)", "formula": "rttMs + keys * workUs / 1000", "format": "number" },
        { "id": "parMs", "label": "Parallel GETs (ms)", "formula": "Math.ceil(keys / Math.max(1, conns)) * (rttMs + workUs / 1000)", "format": "number" },
        { "id": "waitPct", "label": "Share of sequential time spent waiting (%)", "formula": "100 * keys * rttMs / seqMs", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

*Figure 4: With the defaults, the loop takes 25.25 ms, MGET 0.75 ms and ten-at-a-time parallel calls about 2.5 ms.*

The model assumes every trip costs the same round trip, the server does the keys one after another, and parallel calls go out in full waves, with no tail latency or bandwidth limits. Check the defaults by hand: 50 × (0.5 + 0.005) = 25.25 ms for the loop, and 0.5 + 50 × 0.005 = 0.75 ms for one batch.

## The case for measuring instead of memorizing

The strongest objection is that these numbers are old. Norvig's table dates from the early 2000s. Colin Scott's interactive version extrapolates them forward and, for 2020, puts an SSD random read at 16 µs and a disk seek near 2 ms.[^2] NVMe drives beat the ~100 µs figure. A round trip inside one rack can come in under 0.5 ms, and a call across availability zones usually costs more. So, the argument goes, measure your own system and ignore the folklore.

That's right for tuning. If you're deciding between two pipeline sizes, measure. It's wrong for design. The gaps between tiers are factors of a thousand, and hardware drift moves each number by a factor of two to five. Whether your SSD reads in 16 µs or 100 µs, a design that makes 50 sequential network calls is still the slow one. The ratio survives the drift, and the ratio is what you need in a design review before anything exists to measure.

## When batching is the wrong fix

The round-trip tax isn't always the bottleneck. Look for these cases before you rewrite a loop.

- **The server work dominates.** One slow SQL query, a large `ZRANGE`, or a value that has to be deserialized on the client costs more than the trip. Batching saves 0.5 ms per call. It won't save a 40 ms query.
- **The payload is big.** At 1 Gbps, 1 MB takes 8 ms to transfer, the cost of 16 round trips. Fifty 100 KB values in one `MGET` is a 5 MB reply, and that time is bandwidth, which batching doesn't reduce.
- **The batch is too big.** Redis queues every pipelined reply in memory until the client reads it. Its docs suggest batches of a reasonable size, such as 10k commands.
- **The keys live on different cluster nodes.** In Redis Cluster, `MGET` and pipelines must stay within one hash slot, or the server returns a `CROSSSLOT` error. Hash tags such as `{user:42}:cart` put related keys in one slot. Unrelated keys need one batch per node.
- **Each call depends on the previous answer.** A read, compute, write sequence can't be pipelined because the client needs the read before it can write. A Lua script runs the whole sequence inside Redis in one trip.
- **Parallel fan-out makes the tail worse.** If 1 call in 100 is slow, a request that waits on 50 parallel calls hits at least one slow call about 39% of the time (1 − 0.99^50). Dean and Barroso's "The Tail at Scale" is about exactly this. Parallel calls cut the average, and p99 can get worse.
- **Local caching serves stale data.** Every instance holds its own copy, so a price change reaches users at different times, and memory grows with each instance. In my experience a TTL of a few seconds covers most read-heavy config. Data where staleness costs money shouldn't be cached this way at all.

## What to measure

Count network calls per request. A tracing tool shows them as spans. If a request has 50 spans to the same dependency, laid end to end, you've found the round-trip tax. Compare the sum of client-side call time with the server's own timing. Redis `SLOWLOG` records only time spent executing, not I/O, so a fast `SLOWLOG` next to a slow client call means the time went to the wire or the queue. Track p99 per dependency, since averages hide the slow trip, as the [latency vs throughput](../latency-vs-throughput/) note shows.

## References

**Articles and papers**
- Peter Norvig, [Teach Yourself Programming in Ten Years](https://norvig.com/21-days.html), with the table of approximate timings for operations on a typical PC.
- Colin Scott, [Latency Numbers Every Programmer Should Know (interactive)](https://colin-scott.github.io/personal_website/research/interactive_latency.html).
- Jeffrey Dean and Luiz André Barroso, [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/), Communications of the ACM, 2013.

**Documentation**
- [Redis pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/).
- [Redis MGET](https://redis.io/docs/latest/commands/mget/).
- [Redis multi-key operations](https://redis.io/docs/latest/develop/using-commands/multi-key-operations/), on hash slots and `CROSSSLOT`.

[^1]: The 9,000 km figure is a rough great-circle distance from California to the Netherlands. Real cables take longer routes, and routers and queues add more, which is why measured round trips land near 150 ms and not 90.
[^2]: Scott's page fits exponential curves to older data points rather than measuring each year, and its source notes that some of the assumptions are rough. Treat its numbers as estimates too.
