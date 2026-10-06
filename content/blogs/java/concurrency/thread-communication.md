---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Thread Communication"
tags: [java, concurrency, threading]
categories: [Java]
mermaid: true
---

Threads coordinate through a shared condition guarded by a lock. `wait()` releases the monitor and parks; `notifyAll()` wakes the waiters, and each one must take the monitor back and re-check the condition in a `while` loop. `sleep()` keeps every lock it holds, while `wait()` gives up its monitor. Cancellation in Java is cooperative: `interrupt()` only sets a flag, blocking calls turn it into `InterruptedException`, and code that swallows that exception is the usual reason an app hangs on shutdown.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Synchronization basics](synchronization-basics.md).

## wait and notifyAll

```java
void awaitReady() throws InterruptedException {
    synchronized (lock) {
        while (!ready) lock.wait();   // releases lock while parked
    }
}

void markReady() {
    synchronized (lock) {
        ready = true;                 // change the condition first
        lock.notifyAll();
    }
}
```

{{< mermaid >}}
sequenceDiagram
  participant A as Thread A (waiter)
  participant M as Monitor (lock)
  participant B as Thread B (signaller)
  A->>M: lock, check ready (false)
  A->>M: wait() releases lock
  B->>M: lock, set ready = true
  B->>M: notifyAll(), unlock
  M-->>A: wake up
  A->>M: reacquire lock, recheck ready (true)
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "wait / notifyAll handoff",
  "subtitle": "The lock changes hands twice",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "boxes": {
    "a":       [30, 150, 190, 190, "Thread A (waiter)"],
    "monitor": [320, 150, 480, 190, "Monitor"],
    "b":       [610, 150, 770, 190, "Thread B"]
  },
  "wires": [
    [[190,170],[320,170]],
    [[480,170],[610,170]],
    [[400,190],[400,250]],[[400,250],[110,250]],[[110,250],[110,190]]
  ],
  "moves": [
    { "start": 0,   "end": 24,  "path": [[190,170],[320,170]], "color": "primary", "label": "lock, ready=false" },
    { "start": 30,  "end": 52,  "path": [[320,170],[190,170]], "color": "primary", "label": "wait(): release lock" },
    { "start": 62,  "end": 86,  "path": [[610,170],[480,170]], "color": "secondary", "label": "lock, ready=true" },
    { "start": 92,  "end": 124, "path": [[400,190],[400,250],[110,250],[110,190]], "color": "secondary", "label": "notifyAll()" },
    { "start": 134, "end": 160, "path": [[190,170],[320,170]], "color": "primary", "label": "reacquire, recheck" }
  ],
  "captions": [
    { "start": 0,   "end": 58,  "text": "A takes the lock, sees ready=false, and wait() gives the lock up", "color": "primary" },
    { "start": 58,  "end": 128, "text": "B takes the lock, sets ready=true, then wakes the waiters", "color": "secondary" },
    { "start": 128, "end": 999, "text": "A must win the lock back and check ready again before going on", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

- You must hold the monitor to call `wait` or `notify`, or you get `IllegalMonitorStateException`.
- Loop on the condition for two reasons. The JVM allows spurious wakeups, and another thread can grab the lock between the notify and your reacquire and flip the condition back.
- The condition is a field (`ready`). Treating "a notify happened" as the condition breaks. If `markReady()` runs before anyone waits, a bare `wait()` sleeps forever (the lost wakeup). The `while (!ready)` check sees `true` and never waits.
- `notify()` wakes one arbitrary thread. When producers and consumers wait on the same monitor for different conditions, it can wake the wrong kind and stall everyone. Default to `notifyAll()`.

Modern code mostly uses `BlockingQueue`, `CountDownLatch` or `Condition`, all built on this same pattern.

## join, sleep, yield

| Call | Effect | Releases locks |
|---|---|---|
| `t.join()` | waits until `t` terminates | n/a |
| `Thread.sleep(ms)` | pauses the current thread | **no**, keeps all monitors |
| `lock.wait(ms)` | pauses and gives up the monitor | yes, that one monitor |
| `Thread.yield()` | scheduler hint, mostly useless | no |

If thread A holds `lock` and calls `sleep(5000)`, every other thread that wants `lock` sits in `BLOCKED` for five seconds. If it calls `lock.wait(5000)` instead, they can take the lock right away. `join()` is also a happens-before edge, so after it returns you see every write the joined thread made. For spin loops, use `Thread.onSpinWait()` instead of `yield()`.

## Interrupts

`t.interrupt()` sets a flag on `t`. What happens next depends on what `t` is doing:

- Blocked in `sleep`, `wait`, `join`, `queue.take()` or `lockInterruptibly()`: it throws `InterruptedException` and clears the flag.
- Running normal code: nothing, until the code checks `Thread.currentThread().isInterrupted()`.
- Waiting to enter `synchronized`, or reading from a classic `java.io` socket: it stays stuck. NIO channels do respond, by closing the channel.

`Thread.interrupted()` checks and clears the flag. `isInterrupted()` only checks.

```java
while (!Thread.currentThread().isInterrupted()) {
    try {
        queue.take().process();
    } catch (InterruptedException e) {
        log.warn("interrupted", e);   // bug: flag was cleared, loop runs forever
    }
}
```

`take()` cleared the flag when it threw, so the loop condition stays true and the worker goes straight back to `take()`. `shutdownNow()`, `future.cancel(true)` and Spring's graceful shutdown all rely on interrupts, so this worker keeps the app alive until the shutdown timeout kills it. Either let the exception propagate, or restore the flag with `Thread.currentThread().interrupt()` and exit the loop.

Producer-consumer gets its own walkthrough in [Classic problems](classic-problems.md).
