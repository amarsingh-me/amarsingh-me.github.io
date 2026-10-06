---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Classic Problems"
tags: [java, concurrency, threading]
categories: [Java]
---

Five classic problems cover most of what interviews ask. **Producer-consumer** is a bounded buffer where producers block when it's full and consumers block when it's empty. In real code that's a `BlockingQueue`. **Dining philosophers** is a deadlock through circular wait, fixed by taking forks in a global order. **Readers-writers** is about letting readers share while writers get exclusive access, without starving the writers. **Sleeping barber** is a bounded waiting room where customers leave if it's full, which maps neatly onto `offer()` and `take()`. **Odd/even printing** is two threads taking strict turns on one shared condition.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Uses [Thread communication](thread-communication.md), [Locks](locks.md) and [Concurrent collections](concurrent-collections.md).

## Producer-consumer

{{< moving-diagram >}}
{
  "title": "Producer-consumer",
  "subtitle": "A bounded buffer decouples the two speeds",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "boxes": {
    "producer": [30, 150, 190, 190, "Producer"],
    "buffer":   [320, 150, 480, 190, "Buffer (cap 3)"],
    "consumer": [610, 150, 770, 190, "Consumer"]
  },
  "wires": [
    [[190,170],[320,170]],
    [[480,170],[610,170]]
  ],
  "moves": [
    { "start": 0,   "end": 18,  "path": [[190,170],[320,170]], "color": "primary", "label": "put #1" },
    { "start": 22,  "end": 40,  "path": [[190,170],[320,170]], "color": "primary", "label": "put #2" },
    { "start": 44,  "end": 62,  "path": [[190,170],[320,170]], "color": "primary", "label": "put #3" },
    { "start": 80,  "end": 104, "path": [[480,170],[610,170]], "color": "secondary", "label": "take #1" },
    { "start": 110, "end": 128, "path": [[190,170],[320,170]], "color": "primary", "label": "put #4" },
    { "start": 140, "end": 164, "path": [[480,170],[610,170]], "color": "secondary", "label": "take #2" }
  ],
  "captions": [
    { "start": 0,   "end": 66,  "text": "the producer is faster and fills all 3 slots", "color": "primary" },
    { "start": 66,  "end": 106, "text": "buffer full: put #4 blocks until the consumer takes one", "color": "secondary" },
    { "start": 106, "end": 999, "text": "each take frees a slot and wakes the blocked producer", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

By hand, with `wait`/`notifyAll`:

```java
class BoundedBuffer<T> {
    private final Queue<T> items = new ArrayDeque<>();
    private final int capacity;
    BoundedBuffer(int capacity) { this.capacity = capacity; }

    synchronized void put(T item) throws InterruptedException {
        while (items.size() == capacity) wait();
        items.add(item);
        notifyAll();            // producers and consumers share one wait set
    }

    synchronized T take() throws InterruptedException {
        while (items.isEmpty()) wait();
        T item = items.remove();
        notifyAll();
        return item;
    }
}
```

In real code:

```java
BlockingQueue<Order> queue = new ArrayBlockingQueue<>(100);
queue.put(order);              // producer
Order o = queue.take();        // consumer
```

To stop consumers, put a **poison pill** (a sentinel object) on the queue for each consumer, or interrupt them.

## Dining philosophers

Five philosophers sit at a round table with five forks. Each one picks up the left fork, then the right. If all five pick up their left fork at once, each waits for a right fork held by a neighbour, and that's a deadlock.

```java
int first  = Math.min(left, right);   // lower-numbered fork first
int second = Math.max(left, right);
forks[first].lock();
try {
    forks[second].lock();
    try { eat(); } finally { forks[second].unlock(); }
} finally { forks[first].unlock(); }
```

Taking forks in a global order breaks the circular wait. Two other fixes work too: a `Semaphore(4)` that lets at most four philosophers reach for forks at once, or `tryLock` with a random backoff.

## Readers-writers

Many readers can read together, while a writer needs everyone else out. `ReentrantReadWriteLock` solves exactly this. The design question is who gets priority: readers first can starve writers, and writers first can starve readers. `new ReentrantReadWriteLock(true)` makes it fair. Details in [Locks](locks.md).

## Sleeping barber

One barber, N waiting chairs. The barber sleeps when nobody's waiting, and a customer who finds every chair taken leaves.

```java
BlockingQueue<Customer> chairs = new ArrayBlockingQueue<>(N);

// customer
if (!chairs.offer(me)) leave();         // full: don't wait, just go

// barber
while (true) cut(chairs.take());        // take() is the sleep
```

The non-blocking `offer` models "leave if full", and the blocking `take` models "sleep until a customer arrives".

## Printing odd/even with two threads

```java
class OddEven {
    private int n = 1;
    private final int max;
    OddEven(int max) { this.max = max; }

    synchronized void run(int parity) throws InterruptedException {   // 1 = odd, 0 = even
        while (true) {
            while (n <= max && n % 2 != parity) wait();
            if (n > max) { notifyAll(); return; }
            System.out.println(Thread.currentThread().getName() + ": " + n++);
            notifyAll();
        }
    }
}
// new Thread(() -> p.run(1), "odd") and new Thread(() -> p.run(0), "even"), with InterruptedException handled
```

The shared condition is "whose turn is it" (`n % 2`). The `n > max` checks let both threads exit cleanly instead of one waiting forever. Another approach uses two `Semaphore`s, `odd(1)` and `even(0)`: each thread acquires its own semaphore and releases the other's after it prints.
