---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Atomics and CAS"
tags: [java, concurrency, threading]
categories: [Java]
---

Atomic classes (`AtomicInteger`, `AtomicLong`, `AtomicReference` and friends) update one variable atomically without a lock, using the CPU's **compare-and-swap** (CAS) instruction: "set this to B only if it still equals A". On failure the code reads again and retries, so no thread ever blocks. Under heavy contention those retries burn CPU, and for hot counters `LongAdder` is much faster. CAS only compares values, so it can't tell that a value changed from A to B and back to A (the ABA problem). `AtomicStampedReference` fixes that by adding a version number. "Lock-free" means some thread always makes progress, and "wait-free" means every thread finishes in a bounded number of steps.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Synchronization basics](synchronization-basics.md) and [the Java Memory Model](java-memory-model.md).

## Atomic variables

```java
AtomicInteger hits = new AtomicInteger();
hits.incrementAndGet();                       // atomic count++
hits.updateAndGet(v -> Math.min(v + 1, 100)); // atomic capped increment
ref.compareAndSet(expected, newValue);        // the primitive under all of them
```

This is the lock-free fix for the lost-update `Counter` in [Synchronization basics](synchronization-basics.md):

```java
class Counter {
    public AtomicInteger counter = new AtomicInteger();

    public void incrementCounter() {
        counter.incrementAndGet();
    }
}
```

In `RaceConditionExample`, the plain `int` version printed around 11,000 to 12,000. This version printed 20,000 on all three runs, the same as `synchronized`, and no thread ever blocks.

Atomics also give volatile visibility, so a `set()` publishes earlier writes the same way a volatile write does. The function you pass to `updateAndGet` or `accumulateAndGet` **may run several times** when CAS retries, so it must have no side effects.

## How CAS works

```java
int v, next;
do {
    v = value.get();           // 1. read
    next = v + 1;              // 2. compute
} while (!value.compareAndSet(v, next));   // 3. swap if unchanged, else retry
```

On x86 this compiles to one `lock cmpxchg`. ARM uses `CAS` or a load-linked/store-conditional pair. No thread is ever parked, so a thread descheduled in the middle of the loop can't block anyone else.

## Contention and LongAdder

When 32 threads hammer one `AtomicLong`, most CAS attempts fail, and the cache line holding the value keeps bouncing between cores. `LongAdder` spreads updates across several cells (roughly one per contending thread) and adds them up only when you call `sum()`. Use it for metrics and hit counters. The catch is that `sum()` isn't an atomic snapshot, so don't use it for sequence numbers or anything that needs an exact value at a point in time.

## The ABA problem

A lock-free stack pops by doing CAS on `head` from node A to `A.next`. Suppose that between your read and your CAS, another thread pops A, pops B, and pushes A back. `head` equals A again, your CAS succeeds, and `head` now points to B, which has already been removed.

Java's garbage collector prevents the classic form of this bug: a node can't be freed and reused while your thread still holds a reference to it. ABA still bites with reused nodes, object pools, and plain values (an account balance that goes 100 → 50 → 100). The fix is to version the reference:

```java
AtomicStampedReference<Node> head = new AtomicStampedReference<>(null, 0);
int[] stamp = new int[1];
Node h = head.get(stamp);
head.compareAndSet(h, h.next, stamp[0], stamp[0] + 1);   // fails if the version moved
```

`AtomicMarkableReference` is the version with a boolean flag instead of a counter.

## Lock-free vs wait-free

| Guarantee | Meaning | Example |
|---|---|---|
| Blocking | a descheduled lock holder stops everyone | `synchronized` |
| Lock-free | some thread always completes; individuals can retry forever | `ConcurrentLinkedQueue`, CAS loops |
| Wait-free | every thread completes in a bounded number of steps | `getAndIncrement` on x86 (`lock xadd`) |

Lock-free code isn't automatically faster. Under contention, a good lock that parks waiters can beat a CAS loop that spins. Measure before you rewrite.

For CAS on a plain field without wrapping it in an atomic object, use `VarHandle` (Java 9+) or the older `AtomicIntegerFieldUpdater`. `ConcurrentHashMap` uses this approach internally.
