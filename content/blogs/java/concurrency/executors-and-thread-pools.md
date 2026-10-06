---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Executors and Thread Pools"
tags: [java, concurrency, threading]
categories: [Java]
mermaid: true
---

An `ExecutorService` separates *what* to run (a task) from *how* it runs (pooled threads, a queue, a policy for overload). `ThreadPoolExecutor` handles each new task in a fixed order: start a core thread, else queue the task, else start an extra thread up to the maximum, else reject it. So with an unbounded queue, `maximumPoolSize` never takes effect. The `Executors` factory methods hide risky defaults: `newFixedThreadPool` has an unbounded queue that can run you out of memory, and `newCachedThreadPool` has no thread limit. In production, build a `ThreadPoolExecutor` yourself with a bounded queue, named threads, and a rejection policy you chose. Exceptions from `submit()` disappear unless someone calls `get()`, and a scheduled task that throws never runs again.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Fundamentals](fundamentals.md).

## How a task is handled

{{< mermaid >}}
flowchart LR
  S[submit task] --> C{threads below core?}
  C -- yes --> N[start core thread]
  C -- no --> Q{queue has room?}
  Q -- yes --> E[enqueue]
  Q -- no --> M{threads below max?}
  M -- yes --> X[start extra thread]
  M -- no --> R[rejection policy]
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "ThreadPoolExecutor under load",
  "subtitle": "core=1, queue capacity=2, max=2",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 240,
  "boxes": {
    "caller": [30, 150, 150, 190, "Caller"],
    "core":   [600, 40, 760, 80, "Core thread"],
    "queue":  [300, 150, 460, 190, "Queue (cap 2)"],
    "extra":  [600, 230, 760, 270, "Extra thread"],
    "reject": [30, 240, 150, 280, "Rejected"]
  },
  "wires": [
    [[150,170],[220,170]],[[220,170],[220,60]],[[220,60],[600,60]],
    [[220,170],[300,170]],
    [[220,170],[220,250]],[[220,250],[600,250]],
    [[90,190],[90,240]],
    [[460,170],[530,170]],[[530,170],[530,60]],[[530,60],[600,60]]
  ],
  "moves": [
    { "start": 0,   "end": 26,  "path": [[150,170],[220,170],[220,60],[600,60]], "color": "primary", "label": "task 1" },
    { "start": 32,  "end": 50,  "path": [[150,170],[220,170],[300,170]], "color": "secondary", "label": "task 2" },
    { "start": 56,  "end": 74,  "path": [[150,170],[220,170],[300,170]], "color": "secondary", "label": "task 3" },
    { "start": 82,  "end": 110, "path": [[150,170],[220,170],[220,250],[600,250]], "color": "primary", "label": "task 4" },
    { "start": 118, "end": 134, "path": [[90,190],[90,240]], "color": "secondary", "label": "task 5" },
    { "start": 150, "end": 178, "path": [[460,170],[530,170],[530,60],[600,60]], "color": "primary", "label": "task 2" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "task 1: below core size, so a core thread starts", "color": "primary" },
    { "start": 30,  "end": 80,  "text": "tasks 2 and 3: core is busy, so they wait in the queue", "color": "secondary" },
    { "start": 80,  "end": 114, "text": "task 4: queue full, below max, so an extra thread starts", "color": "primary" },
    { "start": 114, "end": 146, "text": "task 5: at max with a full queue, so it is rejected", "color": "secondary" },
    { "start": 146, "end": 999, "text": "when the core thread finishes, it takes task 2 from the queue", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## Building one properly

```java
ThreadPoolExecutor pool = new ThreadPoolExecutor(
    8, 16,                                    // core, max
    60, SECONDS,                              // idle extra threads die after this
    new ArrayBlockingQueue<>(500),            // bounded
    Thread.ofPlatform().name("orders-", 0).factory(),
    new ThreadPoolExecutor.CallerRunsPolicy());
```

Name your threads. A dump full of `pool-7-thread-3` tells you nothing. In Spring, `ThreadPoolTaskExecutor` takes the same settings.

**Sizing:** for CPU-bound work, use about the number of cores. For I/O-bound work, use roughly `cores × (1 + wait time / compute time)`. Then check it with a load test, because the formula is only a starting point. The calculator below runs that formula.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "I/O-bound pool size",
      "inputs": [
        { "id": "cores", "label": "CPU cores", "default": 8, "step": 1 },
        { "id": "wait", "label": "Time waiting on I/O per task", "unit": "ms", "default": 90, "step": 5 },
        { "id": "cpu", "label": "Time computing per task", "unit": "ms", "default": 10, "step": 1 }
      ],
      "outputs": [
        { "id": "threads", "label": "Suggested threads", "formula": "cores * (1 + wait / cpu)" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

## Rejection policies

| Policy | On overload |
|---|---|
| `AbortPolicy` (default) | throws `RejectedExecutionException` |
| `CallerRunsPolicy` | the submitting thread runs the task itself, which slows the producer down (natural backpressure) |
| `DiscardPolicy` | drops the task silently |
| `DiscardOldestPolicy` | drops the oldest queued task and retries |

`CallerRunsPolicy` is usually the right default. Never use it when the submitter is an event-loop thread (Netty, WebFlux), because running a task there stalls every connection on that loop.

## Shutdown and exceptions

```java
pool.shutdown();                                  // no new tasks, finish queued ones
if (!pool.awaitTermination(30, SECONDS)) {
    pool.shutdownNow();                           // interrupt workers, return queued tasks
}
```

Since Java 19, `ExecutorService` is `AutoCloseable`, so a try-with-resources block does the same.

- `execute(task)`: an exception goes to the thread's uncaught exception handler, and the pool replaces the dead worker.
- `submit(task)`: the exception is stored in the `Future`. Nobody calls `get()`, so nobody ever sees it. Wrap tasks with your own try/catch and logging.

## Scheduled executors

- `scheduleAtFixedRate(task, 0, 1, SECONDS)` aims for one start per second. A slow run delays the next one, but runs never overlap.
- `scheduleWithFixedDelay` waits a fixed gap after each run finishes.
- If a run throws, **every later run is cancelled silently.** Always catch exceptions inside scheduled tasks.

Prefer these over `java.util.Timer`, which runs everything on one thread and dies for good on the first exception.

## Future and FutureTask

`Future` lets you `get()` (blocking), `get(timeout)`, `cancel(true)` (interrupts the worker) and `isDone()`. `FutureTask` is the class behind it: a `Runnable` and a `Future` at once, so you can hand it to a plain `Thread`. For chaining results without blocking, see [Async and Fork/Join](async-and-fork-join.md).

Don't pool virtual threads. Use `Executors.newVirtualThreadPerTaskExecutor()` and limit concurrency with a [Semaphore](synchronizers.md).
