---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Synchronizers"
tags: [java, concurrency, threading]
categories: [Java]
---

Synchronizers coordinate *when* threads proceed rather than protecting data. A `Semaphore` caps how many threads do something at once. A `CountDownLatch` lets threads wait until N events have happened, and it's single-use. A `CyclicBarrier` makes N threads wait for each other at a checkpoint, then resets for the next round. A `Phaser` works like a reusable barrier whose parties can join and leave between phases. An `Exchanger` swaps one object between two threads. Most bugs with them come from a `countDown()` or `release()` skipped on an exception path, which leaves other threads waiting forever.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Thread communication](thread-communication.md).

## Semaphore

```java
private final Semaphore permits = new Semaphore(10);   // max 10 concurrent calls

Response callDownstream(Request r) throws InterruptedException {
    permits.acquire();
    try {
        return client.call(r);
    } finally {
        permits.release();
    }
}
```

This is a bulkhead: a slow downstream service can tie up at most 10 of your threads. `tryAcquire(timeout)` lets you fail fast instead of queueing.

A semaphore has **no owner**. Any thread can call `release()`, and each extra release adds a permit, so a double release in a buggy `finally` quietly raises your limit to 11. That's also why a binary semaphore isn't a mutex: a mutex is owned and reentrant, and a semaphore is neither.

## CountDownLatch

```java
CountDownLatch ready = new CountDownLatch(3);
// each of 3 services, after starting:  ready.countDown();
ready.await(30, SECONDS);   // main thread waits for all 3
```

- It's single-use. Once the count reaches zero it stays open, and you can't reset it.
- Put `countDown()` in a `finally`, or a startup that throws leaves `await()` hanging.
- In tests, a latch with count 1 makes a good "start gun": every worker calls `await()`, then the test calls `countDown()` once and they all start together, which raises the odds of exposing a race.

## CyclicBarrier

```java
CyclicBarrier barrier = new CyclicBarrier(4, () -> mergeResults());
// each of 4 workers, per round:  computeChunk(); barrier.await();
```

All four threads block in `await()` until the fourth one arrives. The last thread to arrive runs the optional barrier action, then all four continue and the barrier resets for the next round. It fits iterative work such as simulation steps or parallel matrix passes.

If one party is interrupted or times out, the barrier **breaks**. Every other waiter gets `BrokenBarrierException`, and you have to call `reset()` before reusing it.

## Phaser

```java
Phaser phaser = new Phaser(1);      // register the coordinator
phaser.register();                  // a worker joins
phaser.arriveAndAwaitAdvance();     // like barrier.await()
phaser.arriveAndDeregister();       // a worker leaves; later phases wait for one fewer
```

A `Phaser` covers both the latch and the barrier and lets the number of parties change at runtime. Use it when workers come and go between phases. For a fixed set of parties, a latch or barrier is easier to read.

## Exchanger

Two threads meet at `exchange(x)`, and each gets the other's object. The textbook use is double buffering: a filler thread hands over a full buffer and gets an empty one back from the drainer. You won't need it often.

## Which one

| Need | Use |
|---|---|
| At most N at a time | `Semaphore` |
| Wait until N things happened, once | `CountDownLatch` |
| N threads meet each round, then repeat | `CyclicBarrier` |
| Like a barrier, but parties join and leave | `Phaser` |
| Two threads swap data | `Exchanger` |
