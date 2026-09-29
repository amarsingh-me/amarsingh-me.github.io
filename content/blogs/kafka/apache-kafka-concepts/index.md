---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-17
title: Apache Kafka Concepts
tags: [kafka, event-driven-architecture, messaging, distributed-systems, kafka-connect, kafka-streams, schema-registry, exactly-once]
categories: [Kafka]
mermaid: true
---

Kafka is a distributed, durable, append-only log — not a traditional "consume and delete" message queue. A topic is split into partitions for parallelism, each partition is replicated across brokers (one leader, N followers) for fault tolerance, and consumer groups parallelize reading (each partition read by exactly one consumer within a group). Delivery is at-least-once by default, so consumers must be idempotent — exactly-once is available via transactions. Around this core, an ecosystem (Connect, Streams/ksqlDB, Schema Registry) turns Kafka from "just a log" into a full data-integration and stream-processing platform.

This is written as a step-by-step glossary — each numbered section builds on the terms introduced before it.

## 1. What Kafka actually is

Originally built at LinkedIn (~2010) to handle their firehose of activity/event data, then open-sourced as an Apache project. The core idea: it's not really a message queue in the RabbitMQ/SQS sense (publish → consume → delete) — it's a **distributed, durable, append-only log** that you subscribe to. Nothing gets deleted when a consumer reads it; a consumer just tracks an **offset** (a cursor position) and moves it forward.

That one design choice is why Kafka gets used for three overlapping purposes:
1. **Pub-sub messaging** — decoupling services (producer publishes, N independent consumers read, none know about each other).
2. **A durable system of record** — since nothing is deleted on read, a topic can be the actual source of truth, replayable from the beginning at any time.
3. **A substrate for stream processing** — tools like Kafka Streams / ksqlDB process data directly as it flows through.

It's also fast largely *because* it's simple: appending to the end of a file and reading sequentially forward is about the cheapest I/O pattern that exists (sequential disk/page-cache access), versus a traditional queue's per-message delete/ack bookkeeping.

## 2. Cluster, brokers, and the controller

A Kafka **cluster** is a set of servers called **brokers**. No single broker holds all the data — partitions (see step 4) are spread across brokers so both storage and throughput scale horizontally.

Someone still has to track cluster-wide metadata: which topics/partitions exist, which broker is the leader for each partition, and which brokers are currently alive. Since **KRaft** (Kafka Raft — Kafka 3.x+, and the only mode from Kafka 4.0 onward), a subset of brokers act as **controllers**, forming a Raft quorum that stores this metadata in its own internal log and elects a single active controller. Older deployments used an external **ZooKeeper** ensemble for the same job; KRaft folds that responsibility into Kafka itself, removing the extra system to run and keep in sync.

{{< moving-diagram >}}
{
  "title": "KRaft controller quorum",
  "subtitle": "Metadata pushed to every broker",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "ctrl1": [50, 60, 230, 100, "Controller (active)"],
    "ctrl2": [280, 60, 460, 100, "Controller (standby)"],
    "ctrl3": [510, 60, 690, 100, "Controller (standby)"],
    "brk1":  [50, 250, 230, 290, "Broker 1"],
    "brk2":  [280, 250, 460, 290, "Broker 2"],
    "brk3":  [510, 250, 690, 290, "Broker 3"]
  },
  "wires": [
    [[230,80],[280,80]],
    [[460,80],[510,80]],
    [[140,100],[140,180]],
    [[140,180],[140,250]],
    [[140,180],[370,180]],[[370,180],[370,250]],
    [[140,180],[600,180]],[[600,180],[600,250]]
  ],
  "moves": [
    { "start": 0,  "end": 30,  "path": [[140,100],[140,180],[140,250]], "color": "primary", "label": "metadata" },
    { "start": 36, "end": 66,  "path": [[140,100],[140,180],[370,180],[370,250]], "color": "primary", "label": "metadata" },
    { "start": 72, "end": 102, "path": [[140,100],[140,180],[600,180],[600,250]], "color": "primary", "label": "metadata" }
  ],
  "captions": [
    { "start": 0,   "end": 40,  "text": "a subset of brokers act as controllers, forming a Raft quorum", "color": "primary" },
    { "start": 40,  "end": 106, "text": "the active controller pushes topic/partition/leader metadata to every broker", "color": "primary" },
    { "start": 106, "end": 999, "text": "KRaft folds this into Kafka itself — no separate ZooKeeper ensemble needed", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## 3. Topics

A **topic** is a named stream of records — a category things get published to and read from (e.g. `orders`, `payment-events`).
- **Multi-producer, multi-consumer** — any number of producers can write, any number of independent consumers/consumer groups can read, with no knowledge of each other. This is the actual decoupling mechanism.
- **A record is just bytes** — key, value, optional headers, timestamp. Kafka enforces no schema; if you want structure (Avro/Protobuf/JSON with a defined shape), that's a separate layer (a Schema Registry — step 11), not something Kafka itself understands.
- **A topic is a logical name, not the physical unit of storage or parallelism.** That's partitions.

## 4. Partitions & offsets

A topic is split into **partitions** — ordered, append-only logs, and the actual unit Kafka parallelizes storage and throughput across (not the topic itself). Kafka guarantees ordering **within a partition only** — never across partitions of the same topic.

Every record written to a partition gets a sequential, immutable **offset** — its position in that partition's log. A consumer's "position" is just the offset it has processed up to.

How a record picks its partition:
- **Keyed record** — the default partitioner hashes the key (`hash(key) % numPartitions`), so the same key always lands on the same partition — this is what preserves per-key ordering (e.g. all events for `order-123` stay in order).
- **No key** — Kafka spreads records across partitions (sticky/round-robin) purely for load balancing, with no ordering guarantee between them.

{{< moving-diagram >}}
{
  "title": "Partition routing",
  "subtitle": "Same key, same partition",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 190,
  "boxes": {
    "rec1": [30, 40, 190, 80, "key=order-123"],
    "rec2": [30, 150, 190, 190, "key=order-456"],
    "rec3": [30, 260, 190, 300, "key=order-123"],
    "hash": [280, 150, 420, 190, "hash(key) % partitions"],
    "p0":   [560, 80, 760, 120, "Partition 0"],
    "p1":   [560, 220, 760, 260, "Partition 1"]
  },
  "wires": [
    [[190,60],[240,60]],[[240,60],[240,170]],[[240,170],[280,170]],
    [[190,170],[280,170]],
    [[190,280],[240,280]],[[240,280],[240,170]],[[240,170],[280,170]],
    [[420,170],[480,170]],[[480,170],[480,100]],[[480,100],[560,100]],
    [[480,170],[480,240]],[[480,240],[560,240]]
  ],
  "moves": [
    { "start": 0,   "end": 24,  "path": [[190,60],[240,60],[240,170],[280,170]], "color": "primary", "label": "order-123" },
    { "start": 28,  "end": 52,  "path": [[190,170],[280,170]], "color": "secondary", "label": "order-456" },
    { "start": 56,  "end": 80,  "path": [[190,280],[240,280],[240,170],[280,170]], "color": "primary", "label": "order-123" },
    { "start": 88,  "end": 114, "path": [[420,170],[480,170],[480,100],[560,100]], "color": "primary", "label": "→ P0" },
    { "start": 118, "end": 144, "path": [[420,170],[480,170],[480,240],[560,240]], "color": "secondary", "label": "→ P1" }
  ],
  "captions": [
    { "start": 0,   "end": 84,  "text": "same key always hashes to the same partition — hash(key) % numPartitions", "color": "primary" },
    { "start": 84,  "end": 148, "text": "order-123 always lands on Partition 0; no key means round-robin instead", "color": "primary" },
    { "start": 148, "end": 999, "text": "ordering is only guaranteed within a single partition, never across partitions", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## 5. Producers & delivery guarantees

**Producers** write records to topics. Two settings control how safely:

**`acks`** — how many replicas must confirm a write before the producer considers it successful:
- `acks=0` — fire and forget, don't even wait for the leader. Fastest, weakest.
- `acks=1` — wait for the leader to write it. If the leader dies *before* followers replicate, that message is gone even though the producer got a success response.
- `acks=all` (`-1`) — wait for every replica in the ISR (step 6). Strongest durability, higher latency.

**Idempotent producer** (`enable.idempotence=true`, default in modern clients) — each producer gets a **producer ID** and tags every record with a **sequence number**. If a network hiccup makes the producer retry a send, the broker recognizes the duplicate sequence number and drops it instead of writing the record twice. This is what makes retries safe without the application having to dedupe manually.

{{< mermaid >}}
sequenceDiagram
  participant P as Producer
  participant L as Leader replica
  participant F1 as Follower 1
  participant F2 as Follower 2
  P->>L: send record (acks=all)
  L->>F1: replicate
  L->>F2: replicate
  F1-->>L: ack
  F2-->>L: ack
  L-->>P: ack (all ISR confirmed)
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "acks=all in flight",
  "subtitle": "Producer → leader → followers → ack",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 180,
  "boxes": {
    "producer": [30, 150, 150, 190, "Producer"],
    "leader":   [280, 150, 420, 190, "Leader replica"],
    "f1":       [560, 70, 700, 110, "Follower 1"],
    "f2":       [560, 230, 700, 270, "Follower 2"]
  },
  "wires": [
    [[150,170],[280,170]],
    [[420,170],[490,170]],[[490,170],[490,90]],[[490,90],[560,90]],
    [[490,170],[490,250]],[[490,250],[560,250]]
  ],
  "moves": [
    { "start": 0,   "end": 24,  "path": [[150,170],[280,170]], "color": "primary", "label": "send (acks=all)" },
    { "start": 28,  "end": 50,  "path": [[420,170],[490,170],[490,90],[560,90]], "color": "secondary", "label": "replicate" },
    { "start": 54,  "end": 76,  "path": [[420,170],[490,170],[490,250],[560,250]], "color": "secondary", "label": "replicate" },
    { "start": 80,  "end": 100, "path": [[560,90],[490,90],[490,170],[420,170]], "color": "secondary", "label": "ack" },
    { "start": 104, "end": 124, "path": [[560,250],[490,250],[490,170],[420,170]], "color": "secondary", "label": "ack" },
    { "start": 128, "end": 150, "path": [[280,170],[150,170]], "color": "primary", "label": "ack (all ISR confirmed)" }
  ],
  "captions": [
    { "start": 0,   "end": 26,  "text": "producer sends with acks=all — wait for every replica in the ISR", "color": "primary" },
    { "start": 26,  "end": 128, "text": "the leader replicates to each follower, which pulls and acknowledges", "color": "secondary" },
    { "start": 128, "end": 999, "text": "only once every ISR replica confirms does the producer get its ack", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

**Common question: can messages arrive out of order?** A producer isn't bound to a single partition — it decides per-record where to route via an explicit partition number, key hashing (default), or round-robin when there's no key (step 4). This has two consequences worth being explicit about:
- **Across partitions, there is no ordering guarantee at all.** If message 1 goes to partition 1 and message 2 goes to partition 2, they're independent logs with independent leaders — it's entirely possible for message 2 to be written and read before message 1. This isn't a bug or a race condition to fix; Kafka simply never promised ordering across partitions.
- **Within one partition**, ordering is only automatic if you use the same key for related records (so they always hash to the same partition) *and* `enable.idempotence=true`. Without idempotence, a producer with multiple requests in flight (`max.in.flight.requests.per.connection > 1`) can have a retried record land **after** a later one that succeeded on the first try — reordering the same partition's log. Idempotence prevents this because the broker tracks each producer's sequence numbers and can detect/reject out-of-sequence writes.

So: **same key → same partition → in-order, as long as idempotence is on.** Different keys or no key → no ordering promise between those records, ever.

## 6. Replication, leader election, and ISR

Each partition has a **replication factor** (commonly 3): one broker holds the **leader** replica, the others hold **follower** replicas.
- Followers don't get pushed data — they **pull** from the leader, using the same fetch mechanism a normal consumer uses. No separate replication protocol.
- The set of replicas caught up enough to be trustworthy is the **ISR — in-sync replicas**. A follower that falls too far behind (configurable lag threshold) gets dropped from the ISR until it catches up.
- If the leader dies, a new leader is elected **only from the ISR** — never from a lagging replica, since that could silently lose committed data.

**Gotcha:** `acks=all` only guarantees what "all" currently means. If the ISR has shrunk to just the leader (followers all lagged out), "all" means "one." **`min.insync.replicas`** guards against this — it sets a floor (e.g. 2) below which the leader refuses writes rather than silently downgrading the durability guarantee.

{{< mermaid >}}
sequenceDiagram
  participant Ctrl as Controller
  participant L as Leader (Broker 1)
  participant F as Follower (Broker 2, in ISR)
  Note over L: Broker 1 crashes
  Ctrl->>Ctrl: detect missed heartbeat
  Ctrl->>F: elect as new leader (was in ISR)
  Ctrl-->>Ctrl: update metadata (new leader = Broker 2)
  Note over F: Broker 2 now serves\nproduce/consume for this partition
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Leader election",
  "subtitle": "Only from the ISR",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "ctrl":     [330, 60, 540, 100, "Controller"],
    "leader":   [30, 220, 220, 260, "Leader (Broker 1)"],
    "follower": [580, 220, 780, 260, "Follower (Broker 2)"]
  },
  "wires": [
    [[125,220],[125,150],[430,150],[430,100]],
    [[430,100],[430,150],[680,150],[680,220]]
  ],
  "moves": [
    { "start": 40, "end": 70,  "path": [[430,100],[430,150],[680,150],[680,220]], "color": "primary", "label": "elect as new leader" },
    { "start": 74, "end": 100, "path": [[680,220],[680,150],[430,150],[430,100]], "color": "secondary", "label": "new leader = Broker 2" }
  ],
  "captions": [
    { "start": 0,   "end": 40,  "text": "Broker 1 (the leader) crashes — the controller detects the missed heartbeat", "color": "primary" },
    { "start": 40,  "end": 74,  "text": "a new leader is elected only from the ISR — Broker 2 qualifies", "color": "primary" },
    { "start": 74,  "end": 999, "text": "Broker 2 now serves produce/consume for this partition", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## 7. Consumers & consumer groups

**Consumers** read records; they're organized into **consumer groups**. Within a given group, each partition is read by exactly one consumer — that's how Kafka parallelizes consumption (add more consumers, up to one per partition, for more parallelism).

Each group tracks its own progress independently, via **committed offsets** stored in an internal topic (`__consumer_offsets`). This means multiple, unrelated consumer groups can read the same topic at completely different paces without affecting each other — e.g. a real-time alerting group and a nightly batch-analytics group reading the same `orders` topic.

Default delivery guarantee is **at-least-once** (so consumers must be idempotent — the same event can arrive twice); stronger guarantees are covered in step 10.

## 8. Rebalancing

**Rebalancing** happens whenever consumer group membership changes — a consumer joins, leaves, or crashes (missed heartbeat) — and partitions need to be redistributed among the remaining/new consumers.

{{< mermaid >}}
sequenceDiagram
  participant C1 as Consumer 1
  participant C2 as Consumer 2 (new)
  participant Coord as Group Coordinator (broker)
  C2->>Coord: join group
  Coord->>C1: revoke partitions
  Coord->>Coord: run partition assignor
  Coord->>C1: assign new partition subset
  Coord->>C2: assign new partition subset
  Note over C1,C2: consumption resumes
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Rebalancing",
  "subtitle": "A new consumer joins the group",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "c1":    [30, 80, 190, 120, "Consumer 1"],
    "c2":    [30, 240, 190, 280, "Consumer 2 (new)"],
    "coord": [560, 150, 780, 190, "Group Coordinator"]
  },
  "wires": [
    [[190,100],[350,100],[350,170],[560,170]],
    [[190,260],[350,260],[350,170],[560,170]]
  ],
  "moves": [
    { "start": 0,  "end": 26,  "path": [[190,260],[350,260],[350,170],[560,170]], "color": "primary", "label": "join group" },
    { "start": 30, "end": 56,  "path": [[560,170],[350,170],[350,100],[190,100]], "color": "secondary", "label": "revoke partitions" },
    { "start": 60, "end": 86,  "path": [[560,170],[350,170],[350,100],[190,100]], "color": "secondary", "label": "assign new subset" },
    { "start": 90, "end": 116, "path": [[560,170],[350,170],[350,260],[190,260]], "color": "secondary", "label": "assign new subset" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "Consumer 2 joins the group", "color": "primary" },
    { "start": 30,  "end": 90,  "text": "the coordinator revokes and reassigns partitions among all consumers", "color": "secondary" },
    { "start": 90,  "end": 999, "text": "consumption resumes with the new assignment", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

Older ("eager") rebalancing revokes *all* partitions from *every* consumer before reassigning — a brief stop-the-world pause for the whole group. **Incremental cooperative rebalancing** only moves the partitions that actually need to move, letting unaffected consumers keep processing throughout.

## 9. Retention & log compaction

Retention is configured **per topic**, and controls when old data disappears:
- **Time-based** — e.g. keep records for 7 days, then delete.
- **Size-based** — cap the partition's total size.
- **Compaction** — instead of deleting by age, keep only the **latest value per key**, forever. Used when a topic represents "current state" rather than "history of events" (e.g. a changelog of user profiles, or Kafka Streams' internal changelog topics from step 13). Writing a record with a `null` value for a key (a **tombstone**) marks that key for deletion once compaction runs.

{{< moving-diagram >}}
{
  "title": "Log compaction",
  "subtitle": "Keep only the latest value per key",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "boxes": {
    "writes":     [30, 150, 150, 190, "writes"],
    "log":        [280, 150, 560, 190, "partition log"],
    "compacted":  [630, 150, 780, 190, "after compaction"]
  },
  "wires": [
    [[150,170],[280,170]],
    [[560,170],[630,170]]
  ],
  "moves": [
    { "start": 0,   "end": 20,  "path": [[150,170],[280,170]], "color": "primary", "label": "K1=v1" },
    { "start": 24,  "end": 44,  "path": [[150,170],[280,170]], "color": "primary", "label": "K2=v2" },
    { "start": 48,  "end": 68,  "path": [[150,170],[280,170]], "color": "primary", "label": "K1=v3" },
    { "start": 72,  "end": 92,  "path": [[150,170],[280,170]], "color": "primary", "label": "K3=v4" },
    { "start": 96,  "end": 116, "path": [[150,170],[280,170]], "color": "primary", "label": "K1=v5" },
    { "start": 124, "end": 156, "path": [[560,170],[630,170]], "color": "secondary", "label": "keep latest per key" }
  ],
  "captions": [
    { "start": 0,   "end": 120, "text": "writes append to the log — K1 is overwritten twice, nothing is deleted yet", "color": "primary" },
    { "start": 120, "end": 160, "text": "compaction keeps only the latest value per key: K2=v2, K3=v4, K1=v5", "color": "secondary" },
    { "start": 160, "end": 999, "text": "used when a topic represents current state, not history — e.g. a user-profile changelog", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## 10. Delivery semantics & exactly-once

Three levels, in order of how much work they take to get:
- **At-most-once** — no retries; a message can be lost, never duplicated.
- **At-least-once** — Kafka's default; retries can create duplicates, so consumers must be idempotent.
- **Exactly-once** — built from two pieces: the **idempotent producer** (step 5, dedupes retries on write) plus **transactions**. A transactional producer (given a `transactional.id`) can write to multiple partitions/topics and mark them committed atomically; a consumer with `isolation.level=read_committed` only ever sees records from committed transactions, skipping aborted ones entirely. This is exactly how Kafka Streams gets exactly-once for a *consume → transform → produce* pipeline.

{{< mermaid >}}
sequenceDiagram
  participant Src as Input topic
  participant App as Stream processor (transactional)
  participant Dst as Output topic
  App->>Src: consume batch (isolation.level=read_committed)
  App->>App: transform
  App->>App: beginTransaction()
  App->>Dst: produce results
  App->>Src: commit consumer offsets (as part of txn)
  App->>App: commitTransaction()
  Note over Dst: downstream read_committed\nconsumers only see this\nafter commit succeeds
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Exactly-once",
  "subtitle": "Idempotent producer + transactions",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 140,
  "boxes": {
    "src": [30, 150, 190, 190, "Input topic"],
    "app": [330, 150, 490, 190, "Stream processor"],
    "dst": [620, 150, 780, 190, "Output topic"]
  },
  "wires": [
    [[190,170],[330,170]],
    [[490,170],[620,170]]
  ],
  "moves": [
    { "start": 0,  "end": 24, "path": [[190,170],[330,170]], "color": "primary", "label": "consume (read_committed)" },
    { "start": 30, "end": 54, "path": [[490,170],[620,170]], "color": "secondary", "label": "produce results" },
    { "start": 58, "end": 78, "path": [[330,170],[190,170]], "color": "secondary", "label": "commit offsets (in txn)" },
    { "start": 82, "end": 100,"path": [[490,170],[620,170]], "color": "primary", "label": "commitTransaction()" }
  ],
  "captions": [
    { "start": 0,   "end": 28,  "text": "consume a batch with isolation.level=read_committed", "color": "primary" },
    { "start": 28,  "end": 80,  "text": "transform, then produce results and commit offsets inside one transaction", "color": "secondary" },
    { "start": 80,  "end": 999, "text": "downstream read_committed consumers only see this after the commit succeeds", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## 11. Schema Registry

Kafka itself doesn't understand or enforce record structure — a value is just bytes. A **Schema Registry** (Confluent's, or open-source alternatives) adds that structure back as a separate service: it stores schema definitions (commonly Avro, Protobuf, or JSON Schema), and producer/consumer serializers talk to it.

- A producer's serializer registers (or looks up) the schema, then writes only a small **schema ID** alongside the encoded bytes — not the whole schema on every record.
- A consumer's deserializer fetches the schema by that ID to decode the bytes correctly.
- **Compatibility modes** (backward / forward / full) let the registry reject a schema change that would break existing producers or consumers, giving you safe schema evolution over time.

{{< moving-diagram >}}
{
  "title": "Schema Registry",
  "subtitle": "Schema ID travels with the bytes",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "producer": [30, 150, 170, 190, "Producer"],
    "sr":       [620, 60, 780, 100, "Schema Registry"],
    "topic":    [330, 150, 470, 190, "Kafka topic"],
    "consumer": [560, 150, 720, 190, "Consumer"]
  },
  "wires": [
    [[170,170],[170,80],[620,80]],
    [[170,170],[330,170]],
    [[470,170],[560,170]],
    [[640,150],[640,100]]
  ],
  "moves": [
    { "start": 0,  "end": 24,  "path": [[170,170],[170,80],[620,80]], "color": "primary", "label": "register/lookup schema" },
    { "start": 28, "end": 50,  "path": [[170,170],[330,170]], "color": "primary", "label": "[schema ID][avro bytes]" },
    { "start": 54, "end": 76,  "path": [[470,170],[560,170]], "color": "secondary", "label": "record" },
    { "start": 80, "end": 104, "path": [[640,150],[640,100]], "color": "secondary", "label": "fetch schema by ID" }
  ],
  "captions": [
    { "start": 0,   "end": 52,  "text": "a producer registers or looks up the schema, then writes only a small schema ID alongside the bytes", "color": "primary" },
    { "start": 52,  "end": 80,  "text": "the topic stores the schema ID + encoded bytes, not the whole schema per record", "color": "secondary" },
    { "start": 80,  "end": 999, "text": "a consumer fetches the schema by ID to decode the bytes correctly", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## 12. Kafka Connect

**Kafka Connect** is a framework for moving data in and out of Kafka without writing custom producer/consumer code.
- **Source connectors** pull data from an external system (a database, files, an API) into a Kafka topic.
- **Sink connectors** push data from a Kafka topic into an external system (Elasticsearch, S3, a data warehouse).
- Connectors run as **distributed workers**, and each connector splits its work into parallel **tasks**.

{{< moving-diagram >}}
{
  "title": "Kafka Connect",
  "subtitle": "Source and sink connectors",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 140,
  "boxes": {
    "db":        [20, 150, 130, 190, "Source DB"],
    "src":       [170, 150, 300, 190, "Source Connector"],
    "topic":     [340, 150, 450, 190, "Kafka topic"],
    "sink":      [490, 150, 620, 190, "Sink Connector"],
    "warehouse": [650, 150, 780, 190, "Data Warehouse"]
  },
  "wires": [
    [[130,170],[170,170]],
    [[300,170],[340,170]],
    [[450,170],[490,170]],
    [[620,170],[650,170]]
  ],
  "moves": [
    { "start": 0,  "end": 24,  "path": [[130,170],[170,170]], "color": "primary", "label": "read" },
    { "start": 28, "end": 50,  "path": [[300,170],[340,170]], "color": "primary", "label": "records" },
    { "start": 54, "end": 76,  "path": [[450,170],[490,170]], "color": "secondary", "label": "poll" },
    { "start": 80, "end": 104, "path": [[620,170],[650,170]], "color": "secondary", "label": "write" }
  ],
  "captions": [
    { "start": 0,   "end": 52,  "text": "source connectors pull data from an external system into a Kafka topic", "color": "primary" },
    { "start": 52,  "end": 82,  "text": "sink connectors push data from a topic into an external system", "color": "secondary" },
    { "start": 82,  "end": 999, "text": "connectors run as distributed workers, splitting work into parallel tasks", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## 13. Kafka Streams / ksqlDB

**Kafka Streams** is a client library (not a separate cluster) for processing data directly as it flows through Kafka — reading from input topics, transforming, and writing to output topics. **ksqlDB** puts a SQL layer on top of the same engine, so you can express stream processing as SQL-like queries instead of Java/Scala code.

Stateful operations (aggregations, joins, windowed counts) keep their working state in a local **state store**, which is continuously backed up to an internal **changelog topic** (a compacted topic — step 9) so state survives a crash or gets rebuilt on another instance.

{{< moving-diagram >}}
{
  "title": "Kafka Streams / ksqlDB",
  "subtitle": "State backed by a changelog topic",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 140,
  "boxes": {
    "input":     [30, 150, 150, 190, "raw-clicks"],
    "processor": [260, 140, 460, 200, "Stream processor"],
    "changelog": [300, 50, 460, 90, "Changelog topic"],
    "state":     [300, 250, 420, 290, "Local state store"],
    "output":    [560, 150, 700, 190, "clicks-per-minute"]
  },
  "wires": [
    [[150,170],[260,170]],
    [[380,140],[380,90]],
    [[360,250],[360,200]],
    [[460,170],[560,170]]
  ],
  "moves": [
    { "start": 0,  "end": 24, "path": [[150,170],[260,170]], "color": "primary", "label": "raw-clicks" },
    { "start": 28, "end": 48, "path": [[380,140],[380,90]], "color": "secondary", "label": "backs up state" },
    { "start": 52, "end": 76, "path": [[460,170],[560,170]], "color": "secondary", "label": "clicks-per-minute" }
  ],
  "captions": [
    { "start": 0,   "end": 26,  "text": "Kafka Streams reads from the input topic and processes records as they arrive", "color": "primary" },
    { "start": 26,  "end": 80,  "text": "stateful ops keep state in a local store, backed up to a compacted changelog topic", "color": "secondary" },
    { "start": 80,  "end": 999, "text": "results go to an output topic — state survives a crash or rebuilds on another instance", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## 14. Security basics

Three independent layers, commonly used together:
- **Encryption in transit** — TLS between clients and brokers.
- **Authentication** — proving *who* a client is: SASL mechanisms (PLAIN, SCRAM) or mutual TLS (mTLS, using client certificates).
- **Authorization** — **ACLs** decide what an authenticated principal is allowed to do (produce to topic X, consume from topic Y, create topics, etc.).

{{< moving-diagram >}}
{
  "title": "Security basics",
  "subtitle": "TLS, auth, then an ACL check",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 130,
  "boxes": {
    "client": [30, 150, 170, 190, "Client"],
    "broker": [330, 150, 470, 190, "Broker"],
    "served": [620, 150, 780, 190, "Request served"]
  },
  "wires": [
    [[170,170],[330,170]],
    [[470,170],[620,170]]
  ],
  "moves": [
    { "start": 0,  "end": 22, "path": [[170,170],[330,170]], "color": "primary", "label": "1. TLS handshake" },
    { "start": 26, "end": 48, "path": [[170,170],[330,170]], "color": "primary", "label": "2. SASL/mTLS auth" },
    { "start": 52, "end": 74, "path": [[170,170],[330,170]], "color": "secondary", "label": "3. check ACL" },
    { "start": 78, "end": 100,"path": [[470,170],[620,170]], "color": "secondary", "label": "allowed" }
  ],
  "captions": [
    { "start": 0,   "end": 50,  "text": "TLS encrypts the connection, then the client authenticates via SASL or mTLS", "color": "primary" },
    { "start": 50,  "end": 78,  "text": "the broker checks an ACL for this principal + topic + operation", "color": "secondary" },
    { "start": 78,  "end": 999, "text": "allowed → request served; denied → AuthorizationException", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## 15. Quotas & monitoring

**Quotas** cap the byte-rate (or request rate) a given client/user can push or pull, so one noisy producer or consumer can't starve everyone else sharing the cluster.

The single most important thing to watch operationally is **consumer lag** — the gap between a partition's latest offset and a consumer group's committed offset. Growing lag means a consumer group is falling behind the rate records are being produced. It's typically tracked via Kafka's JMX metrics, exported to Prometheus, and graphed in Grafana (or tools like Burrow built specifically for lag tracking).

## 16. Architecture at a glance

A worked example tying the terms above together: topic `orders`, 3 partitions, replication factor 3, one consumer group (`analytics-group`) with 2 consumers.

{{< moving-diagram >}}
{
  "title": "Architecture at a glance",
  "subtitle": "topic orders — 3 partitions, replication factor 3",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 170,
  "boxes": {
    "p1":   [20, 60, 170, 100, "order-service"],
    "p2":   [20, 240, 170, 280, "payment-service"],
    "ctrl": [330, 20, 470, 60, "Controller (KRaft)"],
    "b1":   [330, 110, 470, 150, "Broker 1 (leads P0)"],
    "b2":   [330, 190, 470, 230, "Broker 2 (leads P1)"],
    "b3":   [330, 270, 470, 310, "Broker 3 (leads P2)"],
    "c1":   [640, 110, 780, 150, "consumer-1 (reads P0)"],
    "c2":   [640, 230, 780, 270, "consumer-2 (reads P1, P2)"]
  },
  "wires": [
    [[170,80],[330,130]],
    [[170,260],[330,290]],
    [[470,40],[500,40]],[[500,40],[500,130]],[[500,130],[470,130]],
    [[500,130],[500,210]],[[500,210],[470,210]],
    [[500,210],[500,290]],[[500,290],[470,290]],
    [[470,130],[640,130]],
    [[470,210],[550,210],[550,250],[640,250]],
    [[470,290],[550,290],[550,250],[640,250]]
  ],
  "moves": [
    { "start": 0,  "end": 26,  "path": [[170,80],[330,130]], "color": "primary", "label": "OrderPlaced → P0" },
    { "start": 32, "end": 52,  "path": [[470,40],[500,40],[500,130],[470,130]], "color": "secondary", "label": "manages" },
    { "start": 56, "end": 80,  "path": [[470,130],[500,130],[500,210],[470,210]], "color": "secondary", "label": "replicate P0" },
    { "start": 84, "end": 108, "path": [[470,130],[640,130]], "color": "primary", "label": "consumer-1 reads P0" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "order-service writes OrderPlaced — it hashes to partition 0, led by Broker 1", "color": "primary" },
    { "start": 30,  "end": 86,  "text": "the controller tracks leadership; Broker 1 replicates P0 to the other brokers", "color": "secondary" },
    { "start": 86,  "end": 999, "text": "leadership is spread round-robin across brokers to balance write load", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

Note how leaders are spread round-robin across brokers (Broker 1 leads P0, Broker 2 leads P1, Broker 3 leads P2) rather than piling onto one broker — that's real Kafka behavior, not a simplification, and it's what keeps write load balanced across the cluster.

## Use cases

### Messaging backbone (decoupled pub-sub)

Kafka replaces point-to-point integrations between services with one shared log. `order-service` publishes to a topic without knowing who reads it; `email-service`, `fraud-detection`, and `analytics` each read independently, at their own pace, and a new consumer can be added later without touching the producer at all.

{{< moving-diagram >}}
{
  "title": "Messaging backbone",
  "subtitle": "Decoupled pub-sub",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 190,
  "boxes": {
    "producer":  [30, 150, 150, 190, "order-service"],
    "topic":     [330, 150, 480, 190, "orders topic"],
    "email":     [640, 70, 760, 110, "email-service"],
    "fraud":     [640, 150, 760, 190, "fraud-detection"],
    "analytics": [640, 230, 760, 270, "analytics"]
  },
  "wires": [
    [[150,170],[330,170]],
    [[480,170],[560,170]],
    [[560,170],[560,90]],[[560,90],[640,90]],
    [[560,170],[640,170]],
    [[560,170],[560,250]],[[560,250],[640,250]]
  ],
  "moves": [
    { "start": 0,   "end": 40,  "path": [[150,170],[330,170]], "color": "primary", "label": "OrderPlaced" },
    { "start": 50,  "end": 82,  "path": [[480,170],[560,170],[560,90],[640,90]], "color": "secondary", "label": "read" },
    { "start": 86,  "end": 112, "path": [[480,170],[560,170],[640,170]], "color": "secondary", "label": "read" },
    { "start": 116, "end": 148, "path": [[480,170],[560,170],[560,250],[640,250]], "color": "secondary", "label": "read" }
  ],
  "captions": [
    { "start": 0,   "end": 50,  "text": "order-service publishes once — it doesn't know who's listening", "color": "primary" },
    { "start": 50,  "end": 152, "text": "email-service, fraud-detection, and analytics each read independently, at their own pace", "color": "secondary" },
    { "start": 152, "end": 999, "text": "A new consumer can be added later without touching the producer", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

### Centralized log aggregation

Many services each emit logs; instead of each one shipping directly to a log store, they all publish to Kafka, and one pipeline reads from Kafka into the actual store (Elasticsearch, S3, a data lake). Kafka absorbs bursts and buffers the store from load spikes it can't otherwise handle in real time.

{{< moving-diagram >}}
{
  "title": "Centralized log aggregation",
  "subtitle": "Fan-in, not fan-out",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 210,
  "boxes": {
    "svcA":     [30, 70, 150, 110, "service A"],
    "svcB":     [30, 150, 150, 190, "service B"],
    "svcC":     [30, 230, 150, 270, "service C"],
    "topic":    [300, 150, 450, 190, "logs topic"],
    "pipeline": [520, 150, 650, 190, "log pipeline"],
    "store":    [690, 150, 780, 190, "log store"]
  },
  "wires": [
    [[150,90],[220,90]],[[220,90],[220,170]],[[220,170],[300,170]],
    [[150,170],[300,170]],
    [[150,250],[220,250]],[[220,250],[220,170]],[[220,170],[300,170]],
    [[450,170],[520,170]],
    [[650,170],[690,170]]
  ],
  "moves": [
    { "start": 0,   "end": 26,  "path": [[150,90],[220,90],[220,170],[300,170]], "color": "primary", "label": "log lines" },
    { "start": 30,  "end": 52,  "path": [[150,170],[300,170]], "color": "primary", "label": "log lines" },
    { "start": 56,  "end": 82,  "path": [[150,250],[220,250],[220,170],[300,170]], "color": "primary", "label": "log lines" },
    { "start": 90,  "end": 118, "path": [[450,170],[520,170]], "color": "secondary", "label": "read" },
    { "start": 122, "end": 150, "path": [[650,170],[690,170]], "color": "secondary", "label": "write" }
  ],
  "captions": [
    { "start": 0,   "end": 86,  "text": "service A, B, and C each publish logs to Kafka instead of shipping straight to a log store", "color": "primary" },
    { "start": 86,  "end": 154, "text": "one pipeline reads from Kafka and writes into the actual store", "color": "secondary" },
    { "start": 154, "end": 999, "text": "Kafka absorbs bursts and buffers the store from spikes it can't handle in real time", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

### Event sourcing

Instead of storing only current state, the topic itself *is* the source of truth — every state change is appended as an event, forever (or compacted to latest-per-key, step 9). Application state is a **materialized view** that's rebuilt by replaying the log from the beginning, which also gives you a full audit trail for free.

{{< moving-diagram >}}
{
  "title": "Event sourcing",
  "subtitle": "The log is the source of truth",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 180,
  "boxes": {
    "app":   [30, 150, 150, 190, "app"],
    "topic": [330, 150, 480, 190, "orders topic (event log)"],
    "view":  [640, 150, 780, 190, "materialized view"]
  },
  "wires": [
    [[150,170],[330,170]],
    [[480,170],[640,170]]
  ],
  "moves": [
    { "start": 0,   "end": 26,  "path": [[150,170],[330,170]], "color": "primary", "label": "OrderPlaced" },
    { "start": 30,  "end": 56,  "path": [[150,170],[330,170]], "color": "primary", "label": "OrderPaid" },
    { "start": 60,  "end": 86,  "path": [[150,170],[330,170]], "color": "primary", "label": "OrderShipped" },
    { "start": 94,  "end": 130, "path": [[480,170],[640,170]], "color": "secondary", "label": "replay from offset 0" }
  ],
  "captions": [
    { "start": 0,   "end": 90,  "text": "every state change is appended as an event — nothing is overwritten", "color": "primary" },
    { "start": 90,  "end": 134, "text": "the materialized view is rebuilt by replaying the log from the beginning", "color": "secondary" },
    { "start": 134, "end": 999, "text": "this also gives you a full audit trail for free", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

### Change Data Capture (CDC)

A CDC connector (e.g. Debezium, run via Kafka Connect — step 12) tails a database's write-ahead log and publishes every row-level change to a Kafka topic in near real time — without the application code ever having to publish anything itself. Downstream, a search index, a cache, and a data warehouse can each independently stay in sync with the source database.

{{< moving-diagram >}}
{
  "title": "Change Data Capture",
  "subtitle": "Debezium via Kafka Connect",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 190,
  "boxes": {
    "db":        [30, 150, 150, 190, "database (WAL)"],
    "connector": [220, 150, 350, 190, "Debezium (Connect)"],
    "topic":     [420, 150, 540, 190, "topic"],
    "search":    [620, 70, 770, 110, "search index"],
    "cache":     [620, 150, 770, 190, "cache"],
    "warehouse": [620, 230, 770, 270, "data warehouse"]
  },
  "wires": [
    [[150,170],[220,170]],
    [[350,170],[420,170]],
    [[540,170],[590,170]],
    [[590,170],[590,90]],[[590,90],[620,90]],
    [[590,170],[620,170]],
    [[590,170],[590,250]],[[590,250],[620,250]]
  ],
  "moves": [
    { "start": 0,   "end": 26,  "path": [[150,170],[220,170]], "color": "primary", "label": "row change" },
    { "start": 30,  "end": 56,  "path": [[350,170],[420,170]], "color": "primary", "label": "CDC event" },
    { "start": 64,  "end": 92,  "path": [[540,170],[590,170],[590,90],[620,90]], "color": "secondary", "label": "sync" },
    { "start": 96,  "end": 118, "path": [[540,170],[590,170],[620,170]], "color": "secondary", "label": "sync" },
    { "start": 122, "end": 150, "path": [[540,170],[590,170],[590,250],[620,250]], "color": "secondary", "label": "sync" }
  ],
  "captions": [
    { "start": 0,   "end": 60,  "text": "a CDC connector tails the database's write-ahead log", "color": "primary" },
    { "start": 60,  "end": 152, "text": "and publishes every row-level change to Kafka in near real time", "color": "primary" },
    { "start": 152, "end": 999, "text": "downstream, the search index, cache, and warehouse each independently stay in sync", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

### Real-time stream processing

Kafka Streams or ksqlDB (step 13) continuously transform, filter, join, and aggregate data as it arrives — e.g. turning a raw `clicks` topic into a `clicks-per-minute` topic — and write the result back to Kafka or out to a live dashboard, with no batch job or nightly cron involved.

{{< moving-diagram >}}
{
  "title": "Real-time stream processing",
  "subtitle": "Kafka Streams / ksqlDB",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 150,
  "boxes": {
    "input":     [30, 150, 150, 190, "raw-clicks"],
    "processor": [260, 140, 460, 200, "Kafka Streams / ksqlDB"],
    "state":     [300, 250, 420, 290, "state store"],
    "output":    [540, 150, 680, 190, "clicks-per-minute"],
    "dashboard": [710, 150, 780, 190, "dashboard"]
  },
  "wires": [
    [[150,170],[260,170]],
    [[360,250],[360,200]],
    [[460,170],[540,170]],
    [[680,170],[710,170]]
  ],
  "moves": [
    { "start": 0,  "end": 26, "path": [[150,170],[260,170]], "color": "primary", "label": "raw-clicks" },
    { "start": 34, "end": 64, "path": [[360,170],[360,170]], "color": "secondary", "label": "filter, group, window" },
    { "start": 72, "end": 98, "path": [[460,170],[540,170]], "color": "secondary", "label": "clicks-per-minute" },
    { "start": 106,"end": 130,"path": [[680,170],[710,170]], "color": "secondary", "label": "live" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "Kafka Streams / ksqlDB continuously transforms data as it arrives", "color": "primary" },
    { "start": 30,  "end": 100, "text": "turning a raw clicks topic into a clicks-per-minute topic", "color": "secondary" },
    { "start": 100, "end": 999, "text": "written back to Kafka or out to a live dashboard — no batch job, no nightly cron", "color": "primary" }
  ]
}
{{< /moving-diagram >}}
