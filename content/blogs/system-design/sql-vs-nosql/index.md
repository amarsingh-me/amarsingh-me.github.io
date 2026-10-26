---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-26T00:00:00+08:00
title: "SQL vs NoSQL: Access Patterns, Not Hype"
tags: [system-design, distributed-systems, postgres]
categories: [System Design]
mermaid: true
---

Pick a database by its access pattern, meaning how your app reads and writes data: which queries run, how often, and keyed by what. SQL databases like Postgres and MySQL keep rows in tables with a fixed schema, and they give you joins, transactions and ad hoc queries nobody planned for. NoSQL is an umbrella term covering key-value, document, wide-column and graph stores. The big distributed ones, DynamoDB and Cassandra, spread data across machines by a key and want each table designed around a query you already know. A query that names the key reads one partition, however large the table gets. A query that doesn't name it has to ask every partition, so a second question usually gets a second table, and you write every row twice. Discord's message store is the standard example. Early on, when queries change every month, SQL's flexibility is worth more than scale you don't need yet.

## The terms

- **Access pattern**: how your app reads and writes data. Which queries run, how often, keyed by what.
- **SQL database**: a relational database (Postgres, MySQL) that keeps rows in tables with a fixed schema. It supports joins, transactions and ad hoc queries you never planned for.
- **NoSQL**: an umbrella term with two readings, "no SQL" or "not only SQL". It covers key-value, document, wide-column and graph stores.
- **Distributed NoSQL stores** (DynamoDB, Cassandra): they want each table designed around a query you already know, with data spread across machines by a key. Ad hoc questions get hard.
- **Partition**: the slice of data stored together under one partition key. A query that names the key reads one partition.

## Why "it scales" is the wrong reason

A single Postgres primary goes a long way. You can [scale it up](../vertical-vs-horizontal-scaling/) to a very large machine, add read replicas for reads, and split big tables with native partitioning. What it can't do out of the box is spread writes across many machines. Distributed NoSQL stores do that from day one. The partition key decides which machine holds a row, so adding machines adds capacity for both reads and writes.

That's a real advantage, and it comes with a condition. The store can only find a row quickly if the query names the partition key. The planner in Postgres can pick an index, join three tables and answer a question you thought of five minutes ago. Cassandra asks you to have thought of the question when you created the table.

So the useful question is which queries your app runs, and whether one of them is so large and so predictable that it needs a store built around it.

## Two queries, two stores

Take a chat app. Messages live in Postgres in the top row and in a wide-column store partitioned by channel in the bottom row. The first query is "latest 50 messages in #general". Both stores answer it with one trip: Postgres uses an index on `(channel_id, created_at)`, and the NoSQL store reads the #general partition.

The second query is "every message user 42 sent". Postgres uses another index on the same table and makes one trip again. The NoSQL store has no user key, so it asks every partition and waits for all of them.

{{< mermaid >}}
sequenceDiagram
  participant A as app
  participant G as #general
  participant R as #random
  participant D as #dev
  A->>G: messages by user 42?
  A->>R: messages by user 42?
  A->>D: messages by user 42?
  G-->>A: matches
  R-->>A: matches
  D-->>A: matches (slowest one sets the response time)
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "SQL vs NoSQL",
  "subtitle": "Same two queries; the NoSQL store is partitioned by channel",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 160,
  "boxes": {
    "app1":    [40, 60, 160, 116, "app"],
    "pg":      [500, 56, 760, 120, "postgres", "tables + joins"],
    "app2":    [40, 232, 160, 288, "app"],
    "general": [500, 180, 760, 220, "#general"],
    "random":  [500, 240, 760, 280, "#random"],
    "dev":     [500, 300, 760, 340, "#dev"]
  },
  "wires": [
    [[160,80],[500,80]],
    [[500,96],[160,96]],
    [[160,252],[320,252],[320,192],[500,192]],
    [[160,252],[500,252]],
    [[160,252],[320,252],[320,312],[500,312]],
    [[500,208],[340,208],[340,268],[160,268]],
    [[500,268],[160,268]],
    [[500,328],[340,328],[340,268],[160,268]]
  ],
  "moves": [
    { "start": 15,  "end": 30,  "path": [[160,80],[500,80]], "color": "primary", "label": "query" },
    { "start": 40,  "end": 55,  "path": [[500,96],[160,96]], "color": "primary", "label": "50 rows" },
    { "start": 15,  "end": 30,  "path": [[160,252],[320,252],[320,192],[500,192]], "color": "primary", "label": "#general" },
    { "start": 40,  "end": 55,  "path": [[500,208],[340,208],[340,268],[160,268]], "color": "primary", "label": "50 rows" },

    { "start": 115, "end": 130, "path": [[160,80],[500,80]], "color": "primary", "label": "query" },
    { "start": 140, "end": 155, "path": [[500,96],[160,96]], "color": "primary", "label": "rows" },
    { "start": 115, "end": 130, "path": [[160,252],[320,252],[320,192],[500,192]], "color": "secondary", "label": "user 42?" },
    { "start": 115, "end": 130, "path": [[160,252],[500,252]], "color": "secondary" },
    { "start": 115, "end": 130, "path": [[160,252],[320,252],[320,312],[500,312]], "color": "secondary" },
    { "start": 140, "end": 155, "path": [[500,208],[340,208],[340,268],[160,268]], "color": "primary" },
    { "start": 140, "end": 155, "path": [[500,268],[160,268]], "color": "primary", "label": "matches" },
    { "start": 140, "end": 155, "path": [[500,328],[340,328],[340,268],[160,268]], "color": "primary" }
  ],
  "tags": [
    { "start": 8,   "end": 110, "x": 400, "y": 18,  "text": "query: latest 50 in #general", "color": "primary" },
    { "start": 110, "end": 230, "x": 400, "y": 18,  "text": "query: all messages by user 42", "color": "secondary" },
    { "start": 0,   "end": 250, "x": 60,  "y": 48,  "text": "SQL", "color": "primary" },
    { "start": 0,   "end": 250, "x": 110, "y": 168, "text": "NoSQL · key = channel", "color": "primary" },
    { "start": 30,  "end": 110, "x": 690, "y": 44,  "text": "nodes read: 1", "color": "primary" },
    { "start": 130, "end": 230, "x": 690, "y": 44,  "text": "nodes read: 1", "color": "primary" },
    { "start": 30,  "end": 110, "x": 690, "y": 168, "text": "partitions read: 1", "color": "primary" },
    { "start": 130, "end": 230, "x": 690, "y": 168, "text": "partitions read: 3", "color": "secondary" },
    { "start": 120, "end": 230, "x": 630, "y": 358, "text": "no user key · ask every partition", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 15,  "text": "Same two queries, two databases", "color": "primary" },
    { "start": 15,  "end": 110, "text": "keyed query: one node, one partition", "color": "primary" },
    { "start": 110, "end": 175, "text": "no user key: ask every partition, wait for all", "color": "secondary" },
    { "start": 175, "end": 999, "text": "Pick the database by its access pattern", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

With three partitions that looks harmless. With hundreds of nodes and thousands of partitions, the unkeyed query touches every machine in the cluster. It's as slow as the slowest machine at that moment, which is the tail-latency problem from [Latency vs Throughput](../latency-vs-throughput/). Run it often and it eats capacity the keyed queries need.

## How Discord did it

Discord's hottest query is "show the latest messages in this channel". In January 2017 their engineering blog described moving messages from MongoDB to Cassandra, built around that one query.

The primary key is `((channel_id, bucket), message_id)`. The partition key is the channel plus a bucket, which is a fixed window of time. Message IDs are Snowflake IDs, which sort by creation time, so inside a partition the messages are already in order. Loading a channel reads the newest bucket of one partition. That cost stays flat however many billions of messages pile up across the cluster.

The bucket is there so a busy channel doesn't grow one partition forever. Every partition lives on a fixed set of replica nodes, so an unbounded partition becomes a hot spot that no amount of new hardware fixes. The trade-off shows up in quiet channels: if nobody has posted in a while, the newest bucket may be empty, and the read has to walk back through older buckets.

In 2023 Discord wrote a follow-up about storing trillions of messages. They moved to ScyllaDB and kept the same data model. The access pattern drove the design both times. The database brand was the part that changed.

The catch is the one from the animation. "Every message user 42 sent" names no channel. On this table it means asking every partition. The standard fix in a wide-column store is a second table keyed by user, written alongside the first.

{{< moving-diagram >}}
{
  "title": "A second table for a second question",
  "subtitle": "Each message is written twice so both queries stay keyed",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "posterFrame": 120,
  "boxes": {
    "app":     [40, 150, 170, 230, "app"],
    "byChan":  [520, 60, 760, 130, "messages_by_channel", "key = channel + bucket"],
    "byUser":  [520, 250, 760, 320, "messages_by_user", "key = user"]
  },
  "wires": [
    [[170,175],[345,175],[345,95],[520,95]],
    [[170,205],[345,205],[345,285],[520,285]],
    [[520,305],[320,305],[320,220],[170,220]]
  ],
  "moves": [
    { "start": 10,  "end": 35,  "path": [[170,175],[345,175],[345,95],[520,95]], "color": "secondary", "label": "write" },
    { "start": 10,  "end": 35,  "path": [[170,205],[345,205],[345,285],[520,285]], "color": "secondary", "label": "write" },
    { "start": 80,  "end": 100, "path": [[170,205],[345,205],[345,285],[520,285]], "color": "primary", "label": "user 42" },
    { "start": 110, "end": 130, "path": [[520,305],[320,305],[320,220],[170,220]], "color": "primary", "label": "rows" }
  ],
  "tags": [
    { "start": 10,  "end": 70,  "x": 250, "y": 130, "text": "1 message, 2 writes", "color": "secondary" },
    { "start": 100, "end": 200, "x": 640, "y": 345, "text": "partitions read: 1", "color": "primary" }
  ],
  "captions": [
    { "start": 0,   "end": 70,  "text": "every new message goes to both tables", "color": "secondary" },
    { "start": 70,  "end": 150, "text": "user 42's messages: one partition of messages_by_user", "color": "primary" },
    { "start": 150, "end": 999, "text": "the second question costs a second copy of each message", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

DynamoDB offers the same thing as a managed feature: a global secondary index is a second copy of the table under a different key, kept up to date asynchronously. You still pay for the extra writes and storage, and reads from it can lag the main table slightly.

## Do the sums

The first section shows what a query without the partition key costs. The second shows what a second table costs instead.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "A query that doesn't name the partition key",
      "inputs": [
        { "id": "partitions", "label": "Partitions (or nodes) the query must ask", "default": 50, "step": 1 },
        { "id": "slowPct", "label": "Chance one partition answers slowly", "default": 1, "step": 0.5, "unit": "%" },
        { "id": "qps", "label": "How often the query runs", "default": 200, "step": 10, "unit": "per second" }
      ],
      "outputs": [
        { "id": "n", "label": "Partitions read per query", "formula": "Math.max(1, Math.floor(partitions))", "format": "number" },
        { "id": "slowKeyed", "label": "Chance a keyed query is slow (%)", "formula": "Math.min(Math.max(slowPct, 0), 100)", "format": "number" },
        { "id": "slowFanout", "label": "Chance this query is slow (%)", "formula": "(1 - Math.pow(1 - slowKeyed / 100, n)) * 100", "format": "number" },
        { "id": "readsKeyed", "label": "Partition reads per second if it were keyed", "formula": "Math.max(0, qps)", "format": "number" },
        { "id": "readsFanout", "label": "Partition reads per second as it is", "formula": "Math.max(0, qps) * n", "format": "number" }
      ]
    },
    {
      "title": "A second table instead",
      "inputs": [
        { "id": "writes", "label": "New messages", "default": 5000, "step": 100, "unit": "per second" },
        { "id": "tables", "label": "Tables each message is written to", "default": 2, "step": 1 },
        { "id": "msgBytes", "label": "Average stored message size", "default": 500, "step": 50, "unit": "bytes" }
      ],
      "outputs": [
        { "id": "t", "label": "Tables", "formula": "Math.max(1, Math.floor(tables))", "format": "number" },
        { "id": "writeRate", "label": "Writes per second across all tables", "formula": "Math.max(0, writes) * t", "format": "number" },
        { "id": "storageDay", "label": "New storage per day, one replica", "formula": "Math.max(0, writes) * 86400 * Math.max(0, msgBytes) * t", "format": "bytes" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

The model assumes each partition is slow independently with the same chance, the query waits for every partition, and each extra table stores a full copy of the message, with replication counted separately. With the defaults, a keyed query is slow 1% of the time and the 50-partition query 1 − 0.99⁵⁰ ≈ 39.5% of the time, and 200 queries a second turn into 10,000 partition reads. Two tables at 5,000 messages a second mean 10,000 writes a second and 5,000 × 86,400 × 500 × 2 = 432 GB a day (402 GiB, which is what the calculator shows) before replication.

## The lines blur

The SQL vs NoSQL split is less sharp than it was ten years ago. Postgres stores JSON in `jsonb` columns and can index inside them (see [GIN indexes for JSONB](../../databases/postgres-gin-indexes-for-jsonb.md)), so a flexible schema doesn't require a document store. DynamoDB has had transactions across items since 2018 (`TransactWriteItems`). MongoDB has supported multi-document transactions since version 4.0. Picking NoSQL no longer means giving up transactions, and picking Postgres doesn't mean a rigid schema for every field.

What hasn't blurred is the partition key. A distributed store with transactions still wants you to know the query ahead of time.

## Choosing

Write down your top five queries before you pick anything, with rough rates for each. Then:

- **Lots of relations, reports, or money moving between accounts**: start with SQL. Joins and multi-row transactions are where relational databases are strongest, and finance teams will ask questions nobody planned for.
- **One huge, predictable read path** (chat history, sessions, carts): a key-value or wide-column store fits, keyed by the thing every request already knows.
- **Both**: a common setup is Postgres as the system of record and a key-value store for the one hot path.

Each choice has a wrong time. NoSQL is the wrong call when queries change every month, because every new question needs a new table and a backfill. Postgres is the wrong call when one keyed write path outgrows the biggest primary you can buy and sharding by hand becomes your main project.

## What to measure

In Postgres, `pg_stat_statements` ranks queries by total time and call count, which gives you the real top five rather than the ones you remember. In a distributed store, track how many partitions each query touches, the size and request rate of the largest partitions, and p99 latency per node. A query that touches every partition, or one partition taking far more traffic than the rest, tells you the key no longer matches the access pattern.
