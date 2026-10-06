---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Locks"
tags: [java, concurrency, threading]
categories: [Java]
---

`ReentrantLock` does what `synchronized` does and adds timed and interruptible acquisition, several `Condition`s per lock, and an optional fair mode. The cost is that you must unlock in a `finally` yourself. `ReentrantReadWriteLock` lets many readers in at once but only one writer, and it only pays off for long, read-heavy critical sections. `StampedLock` adds optimistic reads that take no lock at all, but it isn't reentrant. Fair locks hand over in FIFO order and prevent starvation, at a large throughput cost. The default is unfair because letting new threads barge in avoids a context switch on every handoff. Use `synchronized` by default and reach for these when you need one of their features.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Synchronization basics](synchronization-basics.md) and [Thread communication](thread-communication.md).

## ReentrantLock

```java
private final ReentrantLock lock = new ReentrantLock();

void update() {
    lock.lock();            // outside try: if lock() throws, finally must not unlock
    try {
        // critical section
    } finally {
        lock.unlock();
    }
}
```

What it adds over `synchronized`:

- `tryLock()` and `tryLock(500, MILLISECONDS)` let a thread give up instead of waiting forever. That's one of the deadlock fixes in [Concurrency problems](concurrency-problems.md).
- `lockInterruptibly()` can be cancelled with `interrupt()`. A thread waiting to enter `synchronized` can't be.
- Several `Condition`s on one lock.
- Monitoring through `getQueueLength()`, `isLocked()` and `isHeldByCurrentThread()`.

Before JDK 24, `synchronized` pinned virtual threads to their carrier while blocked, and `ReentrantLock` didn't. That was a real reason to switch. JEP 491 removed the pinning in JDK 24, so on current JDKs the choice comes down to features. More in [virtual threads](../websockets-threading-virtual-threads.md).

## Condition

```java
private final Condition notFull  = lock.newCondition();
private final Condition notEmpty = lock.newCondition();

// producer, holding lock:  while (count == cap) notFull.await();  ...  notEmpty.signal();
// consumer, holding lock:  while (count == 0) notEmpty.await();   ...  notFull.signal();
```

This is `wait`/`notify` with named wait sets. Producers wait on `notFull` and consumers on `notEmpty`, so `signal()` always wakes the right kind of thread, and `notifyAll()` is no longer needed to stay safe. The same rules apply: hold the lock, and re-check the condition in a `while` loop. `ArrayBlockingQueue` is built this way.

## ReadWriteLock

```java
ReadWriteLock rw = new ReentrantReadWriteLock();
rw.readLock().lock();    // shared: many readers at once
rw.writeLock().lock();   // exclusive: no readers, no other writer
```

- It helps when reads far outnumber writes and each read takes a while. For a quick `map.get()`, the extra bookkeeping makes it slower than a plain lock.
- **You can't upgrade.** Taking the write lock while holding the read lock deadlocks, because the writer waits for every reader to leave, including itself. Release the read lock first, then take the write lock and re-check the state.
- Downgrading is allowed: take the read lock while holding the write lock, then release the write lock.

## StampedLock

```java
long stamp = sl.tryOptimisticRead();   // no lock taken
double x = this.x, y = this.y;         // copy fields into locals
if (!sl.validate(stamp)) {             // a writer got in: fall back
    stamp = sl.readLock();
    try { x = this.x; y = this.y; } finally { sl.unlockRead(stamp); }
}
return Math.hypot(x, y);
```

An optimistic read costs about as much as a volatile read, and validation fails only if a write happened in between. It's very fast for small read-mostly state such as coordinates or config values. The catches: it **isn't reentrant** (taking it twice in one thread deadlocks you), it has no `Condition`s, and the code is easy to get wrong.

## Fair vs unfair

| | Unfair (default) | Fair (`new ReentrantLock(true)`) |
|---|---|---|
| Handoff | an arriving thread can barge ahead of the queue | strict FIFO |
| Throughput | high | much lower, often several times |
| Starvation | possible | prevented |

Barging is fast because the lock goes to a thread that is already running, so the system doesn't have to wake the parked queue head first. One surprise: `tryLock()` with no arguments barges even on a fair lock. Use `tryLock(0, SECONDS)` if you need it to respect fairness.
