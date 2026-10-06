---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: CompletableFuture, Fork/Join, Parallel Streams"
tags: [java, concurrency, threading]
categories: [Java]
---

`CompletableFuture` chains asynchronous steps (`thenApply`, `thenCompose`, `thenCombine`, `allOf`) without blocking a thread on every intermediate result. Unless you pass an executor, the `*Async` methods run on `ForkJoinPool.commonPool()`. That's one pool of `cores - 1` threads shared by the whole JVM, including parallel streams, so a blocking HTTP call on it slows down every other user of that pool. Fork/Join splits a large task into subtasks recursively. Each worker keeps its own deque, and idle workers steal from the far end of busy workers' deques. Parallel streams use the same pool. They help for large, CPU-bound, easily split data, and they often make small or I/O-bound work slower.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Executors and thread pools](executors-and-thread-pools.md).

## CompletableFuture

```java
CompletableFuture<User>  user  = supplyAsync(() -> userClient.get(id), ioPool);
CompletableFuture<Order> order = supplyAsync(() -> orderClient.latest(id), ioPool);

CompletableFuture<Page> page = user
    .thenCombine(order, Page::new)               // both done, then merge
    .orTimeout(2, SECONDS)                       // Java 9+
    .exceptionally(ex -> Page.fallback());
```

| Method | Use |
|---|---|
| `thenApply` | transform the result (like `map`) |
| `thenCompose` | next step returns its own future (like `flatMap`) |
| `thenCombine` | merge two independent futures |
| `allOf` / `anyOf` | wait for all or any; `allOf` returns `CompletableFuture<Void>`, so read each result yourself |
| `exceptionally` / `handle` / `whenComplete` | recover, recover-or-map, or observe |

Gotchas:

- **Always pass an executor for I/O.** Otherwise blocking calls fill up the common pool.
- Methods without `Async` (`thenApply`) run on whichever thread completed the previous stage, or on the caller's thread if that stage is already complete. That can put slow work on a thread you didn't expect.
- `join()` throws an unchecked `CompletionException` and `get()` throws a checked `ExecutionException`. Unwrap the cause in both cases.
- `cancel(true)` **does not interrupt** the running task. It only marks the future as cancelled.

## Fork/Join

```java
class Sum extends RecursiveTask<Long> {
    final int[] a; final int lo, hi;
    Sum(int[] a, int lo, int hi) { this.a = a; this.lo = lo; this.hi = hi; }

    protected Long compute() {
        if (hi - lo <= 10_000) {                 // small enough: just do it
            long s = 0; for (int i = lo; i < hi; i++) s += a[i]; return s;
        }
        int mid = (lo + hi) >>> 1;
        Sum left = new Sum(a, lo, mid);
        left.fork();                             // push to my deque
        return new Sum(a, mid, hi).compute() + left.join();
    }
}
```

Fork one half and compute the other half yourself. Calling `fork()` on both wastes the current thread.

## Work stealing

{{< moving-diagram >}}
{
  "title": "Work stealing",
  "subtitle": "Owner works LIFO at the head, thieves steal FIFO from the tail",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 170,
  "boxes": {
    "w1":    [30, 40, 190, 80, "Worker 1 (busy)"],
    "deque": [250, 150, 550, 190, "Worker 1 deque"],
    "w2":    [610, 40, 770, 80, "Worker 2 (idle)"]
  },
  "wires": [
    [[110,80],[110,170]],[[110,170],[250,170]],
    [[550,170],[690,170]],[[690,170],[690,80]]
  ],
  "moves": [
    { "start": 0,   "end": 26,  "path": [[110,80],[110,170],[250,170]], "color": "primary", "label": "fork(): push" },
    { "start": 34,  "end": 60,  "path": [[250,170],[110,170],[110,80]], "color": "primary", "label": "pop newest" },
    { "start": 74,  "end": 104, "path": [[550,170],[690,170],[690,80]], "color": "secondary", "label": "steal oldest" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "worker 1 forks subtasks onto the head of its own deque", "color": "primary" },
    { "start": 30,  "end": 70,  "text": "it pops the newest one back: small, cache-warm work", "color": "primary" },
    { "start": 70,  "end": 999, "text": "idle worker 2 steals the oldest from the tail, usually the biggest chunk", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

The owner and the thieves work at opposite ends of the deque, so they rarely contend. The oldest task is usually the largest unsplit chunk, which means one steal gives the thief plenty of work. Blocking inside a Fork/Join task stops its worker from doing anything else. If you have to block, wrap the call in `ForkJoinPool.managedBlock` so the pool can add a compensating thread.

## Parallel streams

```java
long n = bigList.parallelStream().filter(this::isPrime).count();
```

They're worth trying when **all** of these hold: there are tens of thousands of elements or more, the work per element is CPU-bound, the source splits cheaply (`ArrayList`, arrays, `IntStream.range`), and the operations are stateless.

Avoid them when:

- the source is a `LinkedList`, `Stream.iterate` or I/O-backed, since these split poorly
- the stream is ordered and uses `limit`, `findFirst` or `sorted`
- each element makes a network call (that work belongs on its own executor)
- you write results from `forEach` into a shared `ArrayList`, which is a race; use `collect` instead

For fan-out where subtasks should be cancelled together, look at structured concurrency in [Advanced topics](advanced.md).
