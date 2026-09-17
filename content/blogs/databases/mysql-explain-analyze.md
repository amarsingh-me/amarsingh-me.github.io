---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-08-10
title: "MySQL EXPLAIN ANALYZE vs EXPLAIN"
tags: [mysql, indexing, performance]
categories: [Databases]
---

`EXPLAIN` shows the planner's *estimated* execution plan; `EXPLAIN ANALYZE` actually runs the query and reports *real* timings and row counts per step.

`EXPLAIN` alone is cheap (no execution) but can be wrong when statistics are stale, which is exactly when you need real numbers most.

`EXPLAIN ANALYZE` executes the query, so:
- It's safe for `SELECT`s but can be dangerous on `UPDATE`/`DELETE` — it actually runs them.
- Compare `rows` (estimated) against `actual rows` to spot bad cardinality estimates.
- A big gap between estimated and actual rows on a step is usually the first place to look when a query is slow.
