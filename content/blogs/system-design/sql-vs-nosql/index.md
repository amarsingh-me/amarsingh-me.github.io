---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-27T00:00:00+08:00
title: "SQL vs NoSQL: Access Patterns, Not Hype"
tags: [system-design, distributed-systems, postgres]
categories: [System Design]
mermaid: true
---

A team moves its app to MongoDB so it can handle more users. Then finance asks for a monthly revenue report, and someone writes a 200-line script to do what one SQL `JOIN` would. MongoDB scales fine. The app was asking it a kind of question it wasn't set up to answer. **Pick a database by its access pattern, not by how well it scales.** Big distributed NoSQL stores like DynamoDB and Cassandra serve one known, keyed query very well. A query that names the key reads one partition. A query that doesn't either asks every partition or needs a second table. Early on, when queries change every month, SQL's flexibility is worth more than scale you don't need yet.

## The terms

- **Access pattern**: the queries your app runs most, the key it looks data up by, and how often it reads compared to writes.
- **SQL database**: a relational database (Postgres, MySQL) that keeps rows in tables with a fixed schema. It supports joins, transactions and ad hoc queries you never planned for.
- **NoSQL**: an umbrella term with two readings, "no SQL" or "not only SQL". It covers key-value, document, wide-column and graph stores.
- **Distributed NoSQL stores** (DynamoDB, Cassandra): they want each table designed around a query you already know, with data spread across machines by a key. Ad hoc questions get hard.
- **Partition**: the slice of data stored together under one partition key. A query that names the key reads one partition.

## Why "it scales" is the wrong reason

As the [microservices and scale](../microservices-and-scale/) note argues, a stateless app scales out by running more copies, and they all wait on the same database. You can [scale a Postgres primary up](../vertical-vs-horizontal-scaling/) to a very large machine, add read replicas, and split big tables with native partitioning. What it can't do out of the box is spread writes across many machines.

Distributed NoSQL stores do that from day one. The partition key decides which machine holds a row, so adding machines adds capacity for reads and writes alike. That's a real advantage. The condition is that the store only finds a row quickly when the query names the partition key. The Postgres planner can pick an index, join three tables and answer a question you thought of five minutes ago. Cassandra asks you to have thought of the question when you created the table.

So the question is whether one of your queries is large and predictable enough to need a store built around it.

## Two queries, two stores

Take a chat app, with messages in Postgres (top row) and in a wide-column store partitioned by channel (bottom row). The first query is "latest 50 messages in #general". Both answer it in one trip. Postgres uses an index on `(channel_id, created_at)`. The NoSQL store reads the #general partition.

The second query is "every message user 42 sent". Postgres uses a second index and still makes one trip. The NoSQL store has no user key, so it asks every partition and waits for all of them.

{{< mermaid >}}
sequenceDiagram
  participant A as app
  participant G as general partition
  participant R as random partition
  participant D as dev partition
  A->>G: messages by user 42?
  A->>R: messages by user 42?
  A->>D: messages by user 42?
  G-->>A: matches
  R-->>A: matches
  D-->>A: matches (slowest one sets the response time)
{{< /mermaid >}}

*Figure 1: Without the partition key, the app asks every partition and waits for the slowest reply.*

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

*Figure 2: Both stores answer the keyed query in one trip. Only the NoSQL row has to fan out for the user query.*

With three partitions that looks harmless. With thousands, the unkeyed query touches every machine and is as slow as the slowest one, the tail-latency problem from [Latency vs Throughput](../latency-vs-throughput/). Run it often and it eats capacity the keyed queries need.

## How Discord did it

Discord is the counter-case to the revenue report: a team that picked its NoSQL store because of its access pattern. Its hottest query is "show the latest messages in this channel". By November 2015 it had stored about 100 million messages in MongoDB, and according to the January 2017 post the data and the index no longer fit in RAM and latency became unpredictable.[^1] The team moved messages to Cassandra.

The primary key is `((channel_id, bucket), message_id)`. The partition key is the channel plus a bucket, a fixed window of time. Message IDs are Snowflake IDs, which sort by creation time, so inside a partition the messages are already in order. Loading a channel reads the newest bucket of one partition, and that cost stays flat however many billions of messages pile up across the cluster.

The bucket stops a busy channel from growing one partition forever. Discord sized it at about 10 days of messages, so that even the largest channels stayed under 100 MB per partition. Quiet channels have the opposite problem: a page of history spreads across many buckets, so the team tracked empty buckets per channel to skip them.

The 2023 follow-up shows the key's failure mode. A busy channel concentrates reads on one partition, and the post says a hot partition "frequently affected latency across our entire database cluster". Discord moved the messages to ScyllaDB in 2022 and still partitions them by channel and bucket. The access pattern, and the key built for it, outlived the database.

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

*Figure 3: A second question costs a second copy of every message, and the read becomes keyed again.*

DynamoDB's global secondary index is the managed version. It's a second copy under another key, updated asynchronously, so it can lag a little.

## Do the sums

Compare the two costs: asking every partition, or keeping a second table.

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

*Figure 4: Asking every partition multiplies both the chance of a slow reply and the read load. A second table moves that cost onto writes and storage.*

The model assumes partitions are slow independently with equal chance, the query waits for all of them, and each extra table stores a full copy. With the defaults, a keyed query is slow 1% of the time and the 50-partition query 1 − 0.99⁵⁰ ≈ 39.5% of the time, and 200 queries a second turn into 10,000 partition reads. Two tables at 5,000 messages a second mean 10,000 writes a second and 5,000 × 86,400 × 500 × 2 = 432 GB a day before replication.[^2]

## The lines blur

The SQL vs NoSQL split is less sharp than it was ten years ago. Postgres stores JSON in `jsonb` columns and can index inside them with GIN (see [GIN indexes for JSONB](../../databases/postgres-gin-indexes-for-jsonb.md)), so a flexible schema doesn't require a document store. DynamoDB's `TransactWriteItems` commits up to 100 writes all-or-nothing, though each item costs two writes of capacity, one to prepare and one to commit. MongoDB runs multi-document transactions on replica sets from version 4.0 and on sharded clusters from 4.2.

What hasn't blurred is the partition key. A distributed store with transactions still wants you to know the query ahead of time.

## Back to the revenue report

The report finance wanted looks like this in SQL:

```sql
SELECT a.plan, date_trunc('month', o.paid_at) AS month, sum(o.amount) AS revenue
FROM orders o JOIN accounts a ON a.id = o.account_id
WHERE o.status = 'paid'
GROUP BY 1, 2;
```

In the MongoDB version, orders were modeled as documents for the app's main read path, and nobody planned for grouping by a field in another collection. The 200-line script does the join, grouping and date handling in application code, and must be kept correct as both shapes change.

To be fair to MongoDB, its aggregation pipeline has `$lookup` and `$group`, and a good pipeline would be much shorter than 200 lines. The script mostly shows a data model built for one access pattern being asked about another. That's exactly the risk when you pick a store before you know the questions.

## The case for starting with NoSQL

The other side has a strong argument. DynamoDB has no server to size and no schema migrations. Its latency stays flat as the table grows. Many apps really are key-value at heart: sessions, carts, profiles looked up by ID. If you'll need to spread writes across machines anyway, designing for a partition key on day one costs less than retrofitting sharding onto Postgres later.

That holds when the access pattern is known and stable, as Discord's was. It breaks down while the product is still finding its shape, and every new report or filter becomes a new table and a backfill. My rule of thumb, and it's a judgment call rather than a measurement, is that a young product doesn't know its top five queries yet.[^3]

## When each choice is the wrong call

Write down your top five queries, with rough rates, before you pick anything. Relations, reports or money moving between accounts point to SQL. One huge, predictable read path (chat history, sessions, carts) points to a key-value or wide-column store. Many systems use both: Postgres as the system of record, a key-value store for the hot path.

**NoSQL is the wrong call** when queries change often. You'll see it as a growing list of "second tables", backfill jobs before each feature, scripts like the revenue one, and queries that touch every partition. A hot key fails the other way. One channel, tenant or viral product takes most of the traffic. Its partition's nodes saturate while the rest of the cluster idles.

**Postgres is the wrong call** when one keyed write path outgrows the biggest primary you can buy. You'll see write latency and replication lag climb with traffic, and sharding by hand becomes the team's main project.

## What to measure

In Postgres, `pg_stat_statements` ranks queries by total time and calls, so you get the real top five. In a distributed store, track how many partitions each query touches, the size and request rate of the largest partitions, and p99 latency per node. A query that touches every partition, or one partition taking far more traffic than the rest, tells you the key no longer matches the access pattern.

## References

**Articles**
- Stanislav Vishnevskiy, [How Discord Stores Billions of Messages](https://discord.com/blog/how-discord-stores-billions-of-messages), Discord blog, January 2017.
- [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages), Discord blog, March 2023.

**Documentation**
- [PostgreSQL: JSON types](https://www.postgresql.org/docs/current/datatype-json.html), on `jsonb` and GIN indexing.
- [Amazon DynamoDB transactions: how it works](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html).
- [MongoDB: Transactions](https://www.mongodb.com/docs/manual/core/transactions/).

[^1]: The same post puts Discord's read/write ratio at about 50/50, with highly random reads. So the predictable part is the query's shape (one channel, newest first).
[^2]: The calculator divides by 1,024 and shows about 402 GB for the same number.
[^3]: Discord itself stored messages in MongoDB first and moved them only after passing about 100 million, by which point its main query was clear.
