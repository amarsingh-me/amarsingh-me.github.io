---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-08-11
title: Postgres GIN Indexes for JSONB Containment Queries
tags: [postgres, indexing, jsonb]
categories: [Databases]
---

A GIN index on a `jsonb` column makes `@>` containment queries fast by indexing every key/value pair inside the document, instead of scanning rows.

Without an index, `WHERE data @> '{"status": "active"}'` on a large `jsonb` column forces a sequential scan. Adding `CREATE INDEX ON t USING gin (data)` lets Postgres use the index for containment (`@>`), existence (`?`), and a few other jsonb operators.

Trade-offs:
- Write overhead: every insert/update touching the jsonb column updates the GIN index entries for each key.
- Index size can be large for documents with many keys — `jsonb_path_ops` is a smaller, faster variant if you only need `@>`.

Reference: [PostgreSQL docs — GIN indexes](https://www.postgresql.org/docs/current/gin.html)
