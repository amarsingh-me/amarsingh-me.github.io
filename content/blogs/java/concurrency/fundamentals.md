---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Fundamentals"
tags: [java, concurrency, threading]
categories: [Java]
mermaid: true
---

A Java process has one heap shared by all its threads, and each thread gets its own stack and program counter. A platform `Thread` maps 1:1 to an OS thread, so each one costs about 1MB of reserved stack plus kernel scheduling. Concurrency means tasks overlap in time; parallelism means they run at the same instant on different cores. A race needs only concurrency, so one core is enough to hit it. Watch for three traps: blocking I/O shows up as `RUNNABLE` in a thread dump, `run()` doesn't start a thread, and the JVM kills daemon threads without running their `finally` blocks.

Part of the [Java Concurrency Roadmap](java-concurrency.md).

## Thread states

{{< mermaid >}}
stateDiagram-v2
  [*] --> NEW
  NEW --> RUNNABLE: start()
  RUNNABLE --> BLOCKED: synchronized, monitor taken
  BLOCKED --> RUNNABLE: monitor acquired
  RUNNABLE --> WAITING: wait() / join() / park()
  WAITING --> BLOCKED: notified, needs monitor back
  WAITING --> RUNNABLE: unpark / joined thread ends
  RUNNABLE --> TIMED_WAITING: sleep(ms) / wait(ms)
  TIMED_WAITING --> RUNNABLE: timeout
  RUNNABLE --> TERMINATED: run() returns
{{< /mermaid >}}

- `BLOCKED` only ever means one thing: the thread is trying to enter a `synchronized` block and someone else holds the monitor.
- `WAITING` means the thread parked itself and needs a signal (`notify`, `unpark`, or the joined thread ending). A thread waiting on a `ReentrantLock` also shows as `WAITING`, because that lock uses `park()`. Read the stack trace to tell which.
- A thread stuck in a socket read or a JDBC call shows `RUNNABLE`. The JVM can't see inside native I/O, so 200 "running" threads in a dump can be 200 threads waiting on a slow database.

## Creating threads

`Runnable` returns nothing and can't throw checked exceptions. `Callable<V>` returns a value and can throw. `Thread` takes only a `Runnable`, so a `Callable` goes through an `ExecutorService` or a `FutureTask`. In real code you submit tasks to an executor and rarely call `new Thread()` yourself.

`t.run()` executes the task on the current thread like any method call. Only `t.start()` creates a new thread, and calling it twice throws `IllegalThreadStateException`.

## Context switching

To switch threads, the OS saves one thread's registers and loads another's. That part takes microseconds. The larger cost comes after: the new thread starts with cold CPU caches and TLB entries. This is why one platform thread per request stops scaling at a few thousand threads, and why thread pools and [virtual threads](../websockets-threading-virtual-threads.md) exist.

## Daemon vs user threads

The JVM exits once only daemon threads remain, and it stops them mid-instruction. They get no `InterruptedException` and their `finally` blocks never run, so a daemon thread that flushes a buffer in `finally` loses that data. Call `setDaemon(true)` before `start()`. New threads inherit daemon status from the thread that created them.

The reverse bug shows up more often. Threads from `Executors.newFixedThreadPool` are user threads, so if you forget `shutdown()`, `main()` returns and the JVM keeps running.

## Priorities

Priorities range from 1 to 10 and are only hints. Linux ignores them by default, and virtual threads always run at `NORM_PRIORITY`. Never rely on them for correctness.
