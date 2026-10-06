---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Concurrent Collections"
tags: [java, concurrency, threading]
categories: [Java]
---

Synchronized wrappers (`Collections.synchronizedMap`, `Vector`, `Hashtable`) put one lock around every call. They still need client-side locking for iteration and compound actions, and their iterators throw `ConcurrentModificationException` if the collection changes underneath. Concurrent collections use finer-grained locking or CAS, and their iterators are weakly consistent: they never throw, and they may or may not show recent changes. `ConcurrentHashMap` is the default choice for a shared map. `CopyOnWriteArrayList` suits small, read-mostly lists. A `BlockingQueue` is the standard way to hand work between threads, and `ConcurrentLinkedQueue` is the lock-free option when nothing needs to block.

Part of the [Java Concurrency Roadmap](java-concurrency.md). See also [which collection to use](../which-collection-use.md) for the single-threaded picks.

## ConcurrentHashMap

Since Java 8 it inserts into an empty bucket with a CAS and locks only the head node of a bucket that already has entries. Reads take no lock at all. A bucket longer than 8 entries turns into a small red-black tree.

```java
counts.merge(word, 1, Integer::sum);          // atomic word count
cache.computeIfAbsent(key, this::load);       // atomic load-once
Set<String> seen = ConcurrentHashMap.newKeySet();
```

- It allows **no null keys or values**. If it did, `get()` returning `null` couldn't distinguish "absent" from "mapped to null" without a second call, and that second call would be a race.
- `size()` is only an estimate while other threads are writing.
- The functions you pass to `compute*` and `merge` run under a bucket lock. Keep them short, and never touch the same map inside them ([details](synchronization-basics.md)).
- Bulk operations like `forEach(parallelismThreshold, ...)` and `reduce` can run on the common pool.

## CopyOnWriteArrayList

Every write copies the whole array, and reads and iteration work on an immutable snapshot with no locking. It fits event listener lists and configuration that changes rarely. With a few thousand elements and frequent writes, every write becomes an O(n) copy plus garbage.

## BlockingQueue

| Method | Full or empty queue |
|---|---|
| `put` / `take` | block |
| `offer(e, timeout)` / `poll(timeout)` | wait, then give up |
| `offer` / `poll` | return `false` / `null` immediately |
| `add` / `remove` | throw |

| Variant | Notes |
|---|---|
| `ArrayBlockingQueue` | bounded, one lock for both ends |
| `LinkedBlockingQueue` | separate put and take locks, so better throughput. ⚠️ Default capacity is `Integer.MAX_VALUE`, which is effectively unbounded |
| `SynchronousQueue` | zero capacity; each `put` waits for a `take`. Used by `newCachedThreadPool` |
| `PriorityBlockingQueue` | unbounded, ordered by priority |
| `DelayQueue` | elements become takeable only after their delay expires |
| `LinkedTransferQueue` | `transfer()` waits until a consumer has received the element |
| `LinkedBlockingDeque` | blocking at both ends |

Always give `LinkedBlockingQueue` a capacity. An unbounded queue turns a slow consumer into an `OutOfMemoryError` instead of backpressure. Producer-consumer built on these is in [Classic problems](classic-problems.md).

## ConcurrentLinkedQueue

This is an unbounded, lock-free queue (Michael-Scott algorithm, CAS on head and tail). Use it when consumers poll and do something else if it's empty. `size()` walks the whole queue in O(n), so use `isEmpty()` instead. `ConcurrentSkipListMap` and `ConcurrentSkipListSet` are the sorted concurrent versions.

## Synchronized vs concurrent

| | Synchronized wrapper | Concurrent collection |
|---|---|---|
| Locking | one lock for everything | per bucket, CAS, or copy-on-write |
| Iteration | lock it yourself; fail-fast | weakly consistent; never throws |
| Compound actions | lock it yourself | `putIfAbsent`, `compute`, `merge` |
| Nulls | allowed | not allowed in CHM |
