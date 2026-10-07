---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: Java Concurrency Roadmap
tags: [java, concurrency, threading]
categories: [Java]
---

Threads in one Java process share the heap, and every concurrency problem comes from that. Two threads touching the same mutable state need two guarantees: **mutual exclusion** (only one changes it at a time) and **visibility** (the other thread sees the change). `synchronized` and locks give you both. `volatile` gives only visibility. On top of that, `java.util.concurrent` adds coordination tools, thread pools, and collections that do the locking for you. The most common production bugs are compound actions that look atomic but aren't, and badly sized thread pools.

This page is the map. Each line links to a short note with the details.

## Foundations

1. [Fundamentals](fundamentals.md): process vs thread, thread states, `start()` vs `run()`, context switching, daemon threads, priorities.
2. [Synchronization basics](synchronization-basics.md): shared state and critical sections, race conditions, `synchronized` and monitors, `volatile`, what is and isn't atomic.
3. [Thread communication](thread-communication.md): `wait`/`notifyAll`, `join`/`sleep`, interrupts and cancellation.
4. [Concurrency problems](concurrency-problems.md): deadlock, livelock, starvation, priority inversion, what "thread-safe" means.
5. [Java Memory Model](java-memory-model.md): visibility, happens-before, instruction reordering, CPU caches and barriers.

## Tools from java.util.concurrent

6. [Locks](locks.md): `ReentrantLock`, `ReadWriteLock`, `StampedLock`, `Condition`, fair vs unfair.
7. [Synchronizers](synchronizers.md): `Semaphore`, `CountDownLatch`, `CyclicBarrier`, `Phaser`, `Exchanger`.
8. [Atomics and CAS](atomics-and-cas.md): atomic variables, compare-and-swap, the ABA problem, lock-free vs wait-free.
9. [Executors and thread pools](executors-and-thread-pools.md): `ThreadPoolExecutor` settings, rejection policies, scheduling, `Future`.
10. [Async and Fork/Join](async-and-fork-join.md): `CompletableFuture`, work stealing, parallel streams.
11. [Concurrent collections](concurrent-collections.md): `ConcurrentHashMap`, `CopyOnWriteArrayList`, `BlockingQueue` variants. See also [which collection to use](../which-collection-use.md).

## Beyond the basics

12. [Advanced topics](advanced.md): `ThreadLocal`, structured concurrency, immutability, the actor model. Virtual threads have their own note: [WebSockets, threading and virtual threads](../websockets-threading-virtual-threads.md). Reactive is covered in [WebFlux and reactive programming](../../spring/webflux-reactive-programming.md).
13. [Classic problems](classic-problems.md): producer-consumer, dining philosophers, readers-writers, sleeping barber, odd/even printing.
14. [Debugging and performance](debugging-and-performance.md): thread dumps, deadlock detection, lock contention, Amdahl's law.
