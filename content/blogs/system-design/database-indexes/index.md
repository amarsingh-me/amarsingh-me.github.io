---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-11-01T00:00:00+08:00
title: "Database Indexes: From 2 Seconds to 2 Milliseconds"
tags: [system-design, indexing, performance]
categories: [System Design]
mermaid: true
---

An orders query runs in 5 ms on a laptop with 10,000 test rows. In production, with 20 million rows, the same SQL takes 2 seconds. The SQL didn't change. The table got 2,000 times bigger, and with no index the database has to read all of it. Three terms explain what happened:

- **Full table scan**: with no usable index, the database reads every row of the table and checks each one against the `WHERE` clause.
- **Index**: a sorted copy of one or more columns, kept separately from the table. Each entry points back to its row.
- **B-tree index**: the default index type in Postgres and MySQL (InnoDB). It's a shallow, balanced tree you walk from the root down to your value, and even with millions of rows that's a handful of levels.

**An index turns a cost that grows with the size of the table into one that grows with the depth of a tree, and every write pays for it.** I'll call that the index trade. Reads go from millions of rows to one page per tree level, a handful of page reads. The bill comes on writes. With three indexes, one new row means four writes. Each index also takes disk and memory. So add an index when the plan shows a full scan on a big, read-heavy table. On a write-heavy log table, wait until a real query needs one. The 2 s and 2 ms figures here are illustrative, not a benchmark.

## The book with no index

Picture a 900-page book with no index. To find "replication" you flip every page. That's the scan. With an index, you go to R, read "replication: p. 412" and jump. The cost: every new edition rewrites those back pages, and the book gets thicker.

The Postgres manual uses the same picture. Without an index, it says, the system "would have to scan the entire `test1` table, row by row, to find all matching entries". That's why the query looked fine on the laptop. A scan's work grows with the row count, so a query that's fine on 10,000 rows does 2,000 times the work on 20 million. An index lookup barely notices the difference.

## How a lookup walks the tree

When a query arrives, the planner picks a plan using its statistics about the table. With an index on `user_id`, the plan for `WHERE user_id = 42` is an index scan: read the root, follow the pointer for the range that holds 42, repeat until you hit a leaf, then fetch the row.

{{< mermaid >}}
sequenceDiagram
  participant A as App
  participant P as Planner
  participant I as B-tree on user_id
  participant T as orders table
  A->>P: SELECT ... WHERE user_id = 42
  P->>P: pick Index Scan (stats say few rows match)
  P->>I: read root page
  I->>I: follow pointers down to the leaf for 42
  I->>T: fetch the row the leaf entry points to
  T-->>A: matching row
{{< /mermaid >}}

*Figure 1: An index lookup is a short chain of page reads: root, inner pages, one leaf, then the row itself.*

The animation runs the same query twice. First with no index, then through the tree. Watch the "rows read" counter.

{{< moving-diagram >}}
{
  "title": "Full scan vs index lookup",
  "subtitle": "WHERE user_id = 42 on orders",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 190,
  "boxes": {
    "root": [130, 40, 210, 80, "50"],
    "in25": [60, 120, 140, 160, "25"],
    "in75": [200, 120, 280, 160, "75"],
    "l1":   [20, 200, 85, 240, "1–24"],
    "l2":   [95, 200, 160, 240, "25–49"],
    "l3":   [175, 200, 240, 240, "50–74"],
    "l4":   [250, 200, 315, 240, "75–99"],
    "r0":  [440, 30, 720, 50, "user_id 17"],
    "r1":  [440, 54, 720, 74, "user_id 88"],
    "r2":  [440, 78, 720, 98, "user_id 3"],
    "r3":  [440, 102, 720, 122, "user_id 56"],
    "r4":  [440, 126, 720, 146, "user_id 91"],
    "r5":  [440, 150, 720, 170, "user_id 24"],
    "r6":  [440, 174, 720, 194, "user_id 70"],
    "r7":  [440, 198, 720, 218, "user_id 8"],
    "r8":  [440, 222, 720, 242, "user_id 63"],
    "r9":  [440, 246, 720, 266, "user_id 42"],
    "r10": [440, 270, 720, 290, "user_id 35"],
    "r11": [440, 294, 720, 314, "user_id 99"]
  },
  "wires": [
    [[150,80],[100,120]],
    [[190,80],[240,120]],
    [[85,160],[52,200]],
    [[115,160],[127,200]],
    [[225,160],[207,200]],
    [[255,160],[282,200]],
    [[127,240],[127,280],[420,280],[440,262]]
  ],
  "moves": [
    { "start": 15,  "end": 95,  "path": [[580,24],[580,320]], "color": "secondary", "label": "scan" },
    { "start": 115, "end": 175, "path": [[170,60],[100,140],[127,220],[127,280],[420,280],[460,256]], "color": "primary", "label": "lookup 42" }
  ],
  "tags": [
    { "start": 0,   "end": 250, "x": 170, "y": 28,  "text": "index on user_id", "color": "primary" },
    { "start": 0,   "end": 250, "x": 580, "y": 20,  "text": "orders · 20M rows (12 shown)", "color": "secondary" },
    { "start": 0,   "end": 15,  "x": 580, "y": 340, "text": "rows read: 0", "color": "secondary" },
    { "start": 15,  "end": 35,  "x": 580, "y": 340, "text": "rows read: 5,000,000", "color": "secondary" },
    { "start": 35,  "end": 55,  "x": 580, "y": 340, "text": "rows read: 10,000,000", "color": "secondary" },
    { "start": 55,  "end": 75,  "x": 580, "y": 340, "text": "rows read: 15,000,000", "color": "secondary" },
    { "start": 75,  "end": 112, "x": 580, "y": 340, "text": "rows read: 20,000,000 · ~2 s", "color": "secondary" },
    { "start": 112, "end": 175, "x": 580, "y": 340, "text": "rows read: 0", "color": "primary" },
    { "start": 175, "end": 250, "x": 580, "y": 340, "text": "rows read: 1 · ~2 ms", "color": "primary" }
  ],
  "captions": [
    { "start": 0,   "end": 15,  "text": "same query, 20 million rows", "color": "primary" },
    { "start": 15,  "end": 70,  "text": "no index: read every row and check it", "color": "secondary" },
    { "start": 70,  "end": 112, "text": "42 is found, but the scan keeps going to the end", "color": "secondary" },
    { "start": 112, "end": 180, "text": "index: root 50, then 25, then leaf 25–49, then the row", "color": "primary" },
    { "start": 180, "end": 999, "text": "Index = a few hops, not a full scan", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

*Figure 2: The scan lights every row, including the ones after 42, because the table isn't sorted by `user_id`, so another 42 could be anywhere further down. The lookup touches three tree nodes and one row.*

Why so few hops? Each tree page holds many keys, "often hundreds" according to Markus Winand, so every level multiplies the reach by that number. He writes that "real world indexes with millions of records have a tree depth of four or five".[^depth] Each hop is a page read, and if the upper levels sit in memory, those hops cost RAM reads at ~100 ns rather than SSD reads at ~100 µs. The [latency numbers](../latency-numbers/) note covers why that gap is a factor of a thousand.

You can check which plan you got with `EXPLAIN`. The output below is trimmed and illustrative:

```text
-- before
Seq Scan on orders
  Filter: (user_id = 42)

-- after CREATE INDEX orders_user_id_idx ON orders (user_id)
Index Scan using orders_user_id_idx on orders
  Index Cond: (user_id = 42)
```

`Seq Scan` is the full table scan. The [EXPLAIN ANALYZE](../../databases/mysql-explain-analyze.md) note shows how to compare the planner's estimates with the actual row counts.

## What every write pays

Now the other half of the index trade. An index is a second copy of the data, sorted differently, and the database has to keep it in step with the table. The Postgres manual says it plainly: keeping indexes synchronized "adds overhead to data manipulation operations", and "indexes that are seldom or never used in queries should be removed."

{{< moving-diagram >}}
{
  "title": "One INSERT, four writes",
  "subtitle": "orders with three indexes",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "posterFrame": 140,
  "boxes": {
    "app":   [30, 150, 150, 210, "app", "INSERT"],
    "table": [280, 150, 420, 210, "orders", "table"],
    "i1":    [580, 40, 760, 90, "idx user_id"],
    "i2":    [580, 155, 760, 205, "idx created_at"],
    "i3":    [580, 270, 760, 320, "idx LOWER(email)"]
  },
  "wires": [
    [[150,180],[280,180]],
    [[420,170],[500,65],[580,65]],
    [[420,180],[580,180]],
    [[420,190],[500,295],[580,295]]
  ],
  "moves": [
    { "start": 10,  "end": 40,  "path": [[150,180],[280,180]], "color": "primary", "label": "new row" },
    { "start": 50,  "end": 80,  "path": [[420,170],[500,65],[580,65]], "color": "secondary", "label": "entry" },
    { "start": 60,  "end": 90,  "path": [[420,180],[580,180]], "color": "secondary", "label": "entry" },
    { "start": 70,  "end": 100, "path": [[420,190],[500,295],[580,295]], "color": "secondary", "label": "entry" }
  ],
  "tags": [
    { "start": 0,   "end": 45,  "x": 215, "y": 250, "text": "writes: 0", "color": "primary" },
    { "start": 45,  "end": 80,  "x": 215, "y": 250, "text": "writes: 1", "color": "primary" },
    { "start": 80,  "end": 90,  "x": 215, "y": 250, "text": "writes: 2", "color": "secondary" },
    { "start": 90,  "end": 100, "x": 215, "y": 250, "text": "writes: 3", "color": "secondary" },
    { "start": 100, "end": 200, "x": 215, "y": 250, "text": "writes: 4", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 45,  "text": "the row goes into the table", "color": "primary" },
    { "start": 45,  "end": 110, "text": "then each index gets its own sorted entry", "color": "secondary" },
    { "start": 110, "end": 999, "text": "3 indexes: 1 insert becomes 4 writes", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 3: The table write is one of four. Every index on the table adds another sorted insert, plus the disk and memory to hold it.*

Indexes on expressions cost a little more, because the database computes the expression for each new row. The Postgres docs call them "relatively expensive to maintain" and useful "when retrieval speed is more important than insertion and update speed."

That's why the read/write mix decides whether an index pays off, not the table's size alone. A big orders table that's read on every page load gains far more from an index than it pays. An append-only log table that takes thousands of inserts a second and is read once a day by a report pays the write cost all day for a gain it rarely uses.

## The case for indexing everything up front

The strongest opposing view goes like this. Disk is cheap. A missing index on a hot path is a production incident at 2 a.m.; an extra index is a small cost on writes that nobody notices. So index every foreign key and every column a query might filter on, and stop guessing.

That holds for read-heavy tables with modest write rates, which describes a lot of business data. It's also right that a missing index usually hurts more than a spare one. Where it breaks is write-heavy tables and memory. Each index competes for the same cache as the table, and an unused index still costs on every insert. Postgres adds one more cost. An update that changes any indexed column can't be a heap-only tuple (HOT) update, so it has to add new entries to every index on the table, and each extra index makes that more likely. The manual names this as a reason to drop unused indexes. Indexing everything also misses the composite case below, where the right index depends on the query shape, not on the column list. I'd rather add indexes from the slow-query log and remove the ones that never get used.

## When the index doesn't help

An index exists and the plan still says `Seq Scan`. The usual reasons:

- **Wrong column order.** An index on `(user_id, created_at)` is sorted by `user_id` first. It helps `WHERE user_id = 42`, and `WHERE user_id = 42 AND created_at > ...`. It does little for a filter on `created_at` alone, because those values are spread across the whole index. MySQL's manual says it "cannot use the index to perform lookups if the columns do not form a leftmost prefix of the index."[^skip]
- **A function on the column.** `WHERE LOWER(email) = 'a@b.com'` skips a plain index on `email`, because the index stores `email`, not `LOWER(email)`. An expression index fixes it: `CREATE INDEX ON users (LOWER(email))`.
- **Too many matches.** If a filter matches a large share of the table, like `status = 'shipped'`, jumping from index to table for each match costs more than reading the table in order, and the planner picks the scan. That's often the right call.
- **A leading wildcard.** B-trees help `LIKE 'foo%'` but not `LIKE '%bar'`, per the Postgres docs. Searching inside a value needs a different index type, such as the [GIN index](../../databases/postgres-gin-indexes-for-jsonb.md) that makes JSONB containment queries fast.

The right index depends on the queries you run, not on the schema. The [SQL vs NoSQL](../sql-vs-nosql/) note makes the same point about picking a database by access pattern.

## What to measure

Both sides of the index trade show up in numbers you already have.

- **The plan, before and after.** Run `EXPLAIN ANALYZE` on the hot query and confirm it says `Index Scan`, with actual rows close to the estimate.
- **Unused indexes.** In Postgres, `pg_stat_user_indexes.idx_scan` counts scans per index. One that stays at zero for weeks is pure write cost.
- **Write latency per table**, before and after adding an index. On a write-heavy table, that's the bill.
- **Index size against memory.** If the indexes on a hot table no longer fit in RAM, lookups start paying SSD prices for the upper levels too.

## The takeaway

The index trade, once more: a lookup reads a few pages instead of the whole table, and every index adds a write to each change. Spend it where the reads are. Take candidates from the slow-query log or from `EXPLAIN` showing a `Seq Scan` on a big, read-heavy table. Put the column you filter by equality first in a composite index, and index the expression if the query wraps the column in a function. Then check `idx_scan` a few weeks later and drop the indexes nothing uses. On a write-heavy table, add one only when a real query needs it.

## References

**Documentation**
- [Indexes: Introduction](https://www.postgresql.org/docs/current/indexes-intro.html), PostgreSQL manual.
- [Index Types](https://www.postgresql.org/docs/current/indexes-types.html), PostgreSQL manual. B-tree is the default; hash, GiST, SP-GiST, GIN and BRIN are the others.
- [Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html) and [Indexes on Expressions](https://www.postgresql.org/docs/current/indexes-expressional.html), PostgreSQL manual.
- [Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html), MySQL 8.4 manual.
- [The Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html), MySQL 8.4 manual. "With the exception of spatial indexes, InnoDB indexes are B-tree data structures."

**Books and guides**
- [The Search Tree (B-Tree)](https://use-the-index-luke.com/sql/anatomy/the-tree), Markus Winand, *Use The Index, Luke*.

[^depth]: Winand's own small example uses four keys per page so the levels are easy to see. Real pages hold far more, which is why millions of rows still fit in four or five levels.
[^skip]: Postgres can sometimes use a skip scan here, running one search per distinct leading value. Its docs say this only pays off when the leading column has few distinct values; with many, "the planner will prefer a sequential table scan over using the index."
