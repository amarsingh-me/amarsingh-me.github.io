---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Debugging and Performance"
tags: [java, concurrency, threading, performance]
categories: [Java]
---

A thread dump (`jcmd <pid> Thread.print` or `jstack`) shows each thread's state, stack, and the locks it holds or waits for. Take three dumps a few seconds apart, because threads stuck on the same frame across all three are your problem. Java-level deadlocks are reported automatically at the bottom of the dump, while livelock and starvation only show up by comparing dumps or watching metrics. JFR and async-profiler measure lock contention directly. Most concurrency performance problems come down to holding a hot lock too long or with too coarse a scope. Amdahl's law sets the ceiling: if 5% of the work is serial, no number of cores will make it more than 20× faster.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Concurrency problems](concurrency-problems.md).

## Thread dumps

```bash
jcmd <pid> Thread.print                                    # platform threads, with lock info
jcmd <pid> Thread.dump_to_file -format=json dump.json      # Java 21+, includes virtual threads
kill -3 <pid>                                              # dump goes to the app's stdout
```

In Spring Boot, `/actuator/threaddump` returns the same data. How to read a dump:

- `- locked <0x...>` means this thread holds that monitor.
- `- waiting to lock <0x...>` means it's `BLOCKED` on a monitor. Search for the same address to find the owner.
- `- parking to wait for <0x...> (a ...ReentrantLock$NonfairSync)` means it's waiting on a `java.util.concurrent` lock.
- `RUNNABLE` inside `socketRead0` or a JDBC driver frame means it's waiting on I/O, not using CPU ([Fundamentals](fundamentals.md)).
- `RUNNABLE` on the same line of your own code in every dump, while the process uses 100% of a core, means a spin loop that never exits. The hung `VolatileExample` from [Synchronization basics](synchronization-basics.md) looks like this:
  ```
  java.lang.Thread.State: RUNNABLE
      at VolatileExample.lambda$withoutVolatileVar$1(VolatileExample.java:21)
  ```
  Line 21 is `while(!nonVolatileFlag) {}`. When a busy-wait never ends, check first whether the flag it waits on is missing `volatile`.

## Deadlock detection

`jstack` and `jcmd` end the dump with `Found one Java-level deadlock:` and the full cycle. This covers both monitors and `java.util.concurrent` locks. To check from code, for example in a health check:

```java
long[] ids = ManagementFactory.getThreadMXBean().findDeadlockedThreads();   // null if none
```

There is no automatic detector for livelock, starvation, or a [thread pool waiting on its own tasks](concurrency-problems.md). Look for the same frames across repeated dumps, a queue depth that only grows, or active threads stuck at the maximum.

## Profiling tools

- **JFR (Java Flight Recorder):** start it with `jcmd <pid> JFR.start duration=60s filename=rec.jfr`. Its events include `jdk.JavaMonitorEnter` (time spent blocked), `jdk.ThreadPark`, and `jdk.VirtualThreadPinned`. Open the recording in JDK Mission Control. The overhead is low enough to run in production.
- **async-profiler:** `-e lock` profiles lock contention, and `-e wall` shows where threads spend time, waiting included. It produces flame graphs.
- **VisualVM** gives a quick live view of threads.
- **JMH** for microbenchmarks. Hand-written timing loops get skewed by JIT warm-up and dead-code elimination.

## Contention and lock granularity

If a profile shows threads queueing on one lock, try these in order:

1. **Shorten the hold.** Move I/O, logging, and allocation out of the critical section.
2. **Split the lock.** Use separate locks for independent state, like `LinkedBlockingQueue`'s separate put and take locks.
3. **Stripe it.** Use N locks chosen by `hash(key) % N`, the way pre-Java 8 `ConcurrentHashMap` used segments.
4. **Stop sharing.** Confine data to one thread, use a `LongAdder` for counters, or swap in immutable snapshots through an `AtomicReference`.

**False sharing** is contention without any lock. Two hot fields written by different threads sit on the same 64-byte cache line, so the line bounces between cores. Padding fixes it, as does `@jdk.internal.vm.annotation.Contended` with `-XX:-RestrictContended`. `LongAdder` pads its cells for this reason.

## Amdahl's law

`speedup(N) = 1 / ((1 - p) + p / N)`, where `p` is the fraction of the work that can run in parallel and `N` is the number of cores.

| Parallel share `p` | 4 cores | 16 cores | ∞ cores |
|---|---|---|---|
| 50% | 1.6× | 1.9× | 2× |
| 95% | 3.5× | 9.1× | 20× |
| 99% | 3.9× | 13.9× | 100× |

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Amdahl's law",
      "inputs": [
        { "id": "p", "label": "Parallel fraction (0 to 1)", "default": 0.95, "step": 0.01 },
        { "id": "n", "label": "Cores", "default": 16, "step": 1 }
      ],
      "outputs": [
        { "id": "speedup", "label": "Speedup", "formula": "1 / ((1 - p) + p / n)" },
        { "id": "ceiling", "label": "Ceiling with unlimited cores", "formula": "1 / (1 - p)" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

Code that runs under a contended lock counts as serial. Shrinking critical sections raises `p`, which usually helps more than adding cores.
