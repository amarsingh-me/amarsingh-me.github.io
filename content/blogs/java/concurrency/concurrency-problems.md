---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Deadlock, Livelock, Starvation"
tags: [java, concurrency, threading]
categories: [Java]
mermaid: true
---

A deadlock needs four conditions at once (mutual exclusion, hold-and-wait, no preemption, circular wait), and breaking any one prevents it. In practice you break circular wait by always taking locks in one global order. A livelock is the opposite symptom: threads stay busy retrying and backing off in lockstep, but none of them gets anywhere. Starvation means one thread never gets its turn, usually because of unfair locks, long lock holders, or a thread pool waiting on its own tasks. Priority inversion is a starvation case where a low-priority lock holder blocks a high-priority thread. A class is thread-safe when it stays correct under concurrent calls without the caller adding any locking.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Synchronization basics](synchronization-basics.md).

## Deadlock

```java
void transfer(Account from, Account to, long amt) {
    synchronized (from) {
        synchronized (to) { from.debit(amt); to.credit(amt); }
    }
}
// Thread 1: transfer(a, b)   Thread 2: transfer(b, a)
```

{{< mermaid >}}
flowchart LR
  T1[Thread 1] -- holds --> A((lock a))
  T1 -. waits for .-> B((lock b))
  T2[Thread 2] -- holds --> B
  T2 -. waits for .-> A
{{< /mermaid >}}

Each thread holds one lock and waits for the other, so both wait forever. A `synchronized` deadlock never recovers, and the only way out is restarting the JVM. Postgres behaves differently: it detects deadlocks between transactions and aborts one of them. The JVM has no equivalent.

Fixes, roughly in order of preference:

- **Lock ordering.** Always lock the account with the lower id first. Then the cycle can't form.
  ```java
  Account first = from.id() < to.id() ? from : to;
  Account second = first == from ? to : from;
  synchronized (first) { synchronized (second) { ... } }
  ```
- **`tryLock` with a timeout** (see [Locks](locks.md)). Give up, release what you hold, and retry later.
- **Hold fewer locks.** Don't call unknown code (listeners, callbacks) while holding a lock, since that code might take other locks in the opposite order.

## Livelock

Two threads each grab lock A, `tryLock` lock B, fail, release A, and retry. If they retry on the same schedule, they collide forever while burning CPU. The usual fix is a **random backoff** before each retry, which breaks the symmetry. Ethernet's collision handling uses the same trick.

## Starvation

A starving thread is runnable but never makes progress. Common causes:

- **Unfair locks.** Newly arriving threads keep grabbing the lock ahead of a waiting one. Fair locks fix this at a large throughput cost.
- **Long lock holds.** I/O inside a `synchronized` block holds every other thread up behind it.
- **Writer starvation.** With a steady stream of readers, a `ReadWriteLock` writer may wait a long time.
- **Thread pool starvation deadlock.** This one hits real services. A task in a fixed pool of 10 submits a subtask to the *same* pool and calls `future.get()`. Run 10 such tasks at once and every worker is waiting for a subtask that has no free thread to run on. Use a separate pool for the subtasks, or don't block on them.

## Priority inversion

A low-priority thread holds a lock that a high-priority thread needs. A medium-priority thread then preempts the low one, so the high-priority thread waits on the medium one. NASA's Mars Pathfinder kept resetting in 1997 because of this. The fix there was priority inheritance: the lock holder temporarily runs at the waiter's priority. In Java, priorities are only hints, so you'll rarely hit it directly. The same shape appears whenever an important request waits on a lock held by background work.

## Thread safety

A class is thread-safe if it stays correct under any interleaving of calls, with no locking by the caller. There are three ways to get there:

1. **Don't share.** Keep the object confined to one thread (local variables, one object per request).
2. **Don't mutate.** Immutable objects are always safe to share.
3. **Synchronize** every access to shared mutable state.

The `Counter` class in [Synchronization basics](synchronization-basics.md) is about the smallest class that isn't thread-safe: two threads doing 20,000 increments end at around 12,000. `CounterWithSynchronized` fixes it using strategy 3.

Thread safety comes in levels. `String` is immutable. `ConcurrentHashMap` is thread-safe. `Collections.synchronizedList` is only conditionally safe, because iterating it needs `synchronized (list)` around the loop. `HashMap` and `SimpleDateFormat` aren't safe at all. Under concurrent resizing, a Java 7 `HashMap` could form a cycle and spin a CPU at 100% forever. Use `DateTimeFormatter`, which is immutable.
