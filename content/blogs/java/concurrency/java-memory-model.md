---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: The Java Memory Model"
tags: [java, concurrency, threading]
categories: [Java]
---

The Java Memory Model (JMM) says which writes a read is allowed to see. Without synchronization, the JIT compiler and the CPU can reorder your code and keep values in registers or store buffers, so one thread may see another's writes late, out of order, or never. The JMM's promise is the **happens-before** relation: if action A happens-before action B, B sees A's effects. Unlocking a monitor, writing a `volatile`, `Thread.start()`, `join()` and handing work to a `java.util.concurrent` class all create these edges. A program with no data races behaves as if all threads ran in some single interleaved order. Leave a data race in and all bets are off, which is why double-checked locking without `volatile` is broken.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Synchronization basics](synchronization-basics.md).

## Why visibility breaks

Three layers reorder or delay writes:

- **The JIT compiler.** It may hoist `stop` out of `while (!stop) work();` and turn the loop into `while (true)`, because nothing in that thread changes `stop`.
- **Store buffers.** A core puts its writes in a private buffer before they reach the cache. Other cores can't see them yet.
- **CPU reordering.** Even x86 lets a later read overtake an earlier write. ARM reorders far more.

Hardware cache coherence (MESI) keeps the caches themselves in agreement, so "stale CPU cache" is the wrong mental model. Most real visibility bugs come from the compiler and from store buffers.

The `VolatileExample` in [Synchronization basics](synchronization-basics.md) shows the compiler case directly. Its reader thread spins on a plain flag:

```java
Thread t2 = new Thread(() -> {
    while(!nonVolatileFlag) {}
    System.out.println("Thread 2 completed!");
});
```

With the JIT on, `t2` never sees `nonVolatileFlag = true` and the program hangs. With `-Xint` it finishes. Nothing in this program creates a happens-before edge between `t1`'s write and `t2`'s reads, so the compiler is free to read the flag once. Declaring it `volatile` adds that edge (write hb every later read), and the loop exits.

{{< moving-diagram >}}
{
  "title": "Publishing through a volatile",
  "subtitle": "Simplified: the write is stuck in a store buffer until a fence",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 190,
  "boxes": {
    "core1": [30, 40, 190, 80, "Core 1 (writer)"],
    "buf":   [30, 150, 190, 190, "Store buffer"],
    "mem":   [320, 150, 480, 190, "Shared cache"],
    "core2": [610, 40, 770, 80, "Core 2 (reader)"]
  },
  "wires": [
    [[110,80],[110,150]],
    [[190,170],[320,170]],
    [[480,170],[690,170]],[[690,170],[690,80]]
  ],
  "moves": [
    { "start": 0,   "end": 22,  "path": [[110,80],[110,150]], "color": "primary", "label": "config = load()" },
    { "start": 30,  "end": 56,  "path": [[480,170],[690,170],[690,80]], "color": "secondary", "label": "reads old config" },
    { "start": 70,  "end": 96,  "path": [[190,170],[320,170]], "color": "primary", "label": "volatile write: drain" },
    { "start": 110, "end": 140, "path": [[480,170],[690,170],[690,80]], "color": "primary", "label": "volatile read: new config" }
  ],
  "captions": [
    { "start": 0,   "end": 28,  "text": "core 1 writes config, but it sits in core 1's store buffer", "color": "primary" },
    { "start": 28,  "end": 66,  "text": "core 2 can't see it yet and reads the old value", "color": "secondary" },
    { "start": 66,  "end": 106, "text": "the volatile write forces earlier writes out first", "color": "primary" },
    { "start": 106, "end": 999, "text": "a volatile read that sees the flag also sees config", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

## Reordering you can observe

```java
// x = y = 0
// Thread 1          // Thread 2
x = 1;               y = 1;
r1 = y;              r2 = x;
```

`r1 == 0 && r2 == 0` is a legal result. Each thread's write can still sit in its store buffer when the other thread reads. Making `x` and `y` `volatile` rules this result out.

## Happens-before rules

- **Program order:** each action in a thread happens-before the next action in that thread.
- **Monitor:** an unlock happens-before every later lock of the *same* monitor.
- **Volatile:** a write happens-before every later read of the *same* field.
- **Thread start and join:** `t.start()` happens-before anything `t` does, and everything `t` does happens-before `t.join()` returns.
- **Concurrency utilities:** putting an item into a `BlockingQueue` or `ConcurrentHashMap` happens-before taking it out. Submitting to an executor happens-before the task runs, and the task finishing happens-before `future.get()` returns.
- **Transitivity:** if A hb B and B hb C, then A hb C. This is why plain writes made before a volatile write become visible.

A **data race** is two accesses to the same variable, at least one of them a write, with no happens-before between them.

## Double-checked locking

```java
private static volatile Singleton instance;   // remove volatile and it breaks

static Singleton get() {
    if (instance == null) {
        synchronized (Singleton.class) {
            if (instance == null) instance = new Singleton();
        }
    }
    return instance;
}
```

`new Singleton()` is three steps: allocate memory, run the constructor, assign the reference. Without `volatile`, the assignment can become visible before the constructor's writes, so another thread can see a non-null, half-built object on the unlocked first check. `volatile` has fixed this since Java 5. A simpler fix is the holder idiom, `private static class Holder { static final Singleton I = new Singleton(); }`, because class initialization is already thread-safe.

## Final fields and safe publication

Writes to `final` fields in a constructor are visible to every thread that later sees the object, as long as `this` didn't escape during construction (for example by registering a listener from the constructor). To publish a mutable object safely, use one of these: a static initializer, a `volatile` or `AtomicReference` field, a `final` field, a lock, or a concurrent collection.

## Memory barriers

The JIT turns happens-before into CPU fences. On x86 only the StoreLoad barrier after a volatile write costs anything (a `lock add`), so volatile reads there are about as cheap as plain reads. ARM needs more fences, which is one reason code with a data race can pass every test on an Intel laptop and then fail on Graviton.
