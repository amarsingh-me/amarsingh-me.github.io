---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: Synchronization Basics"
tags: [java, concurrency, threading]
categories: [Java]
---

Threads share the heap, so any field that more than one thread reads and writes needs atomicity, visibility and ordering. A race condition happens when the result depends on how threads interleave. Two shapes cover most of them: read-modify-write (`count++`) and check-then-act (`if (!map.containsKey(k)) map.put(k, v)`). `synchronized` fixes both by giving **mutual exclusion and visibility** on one object's monitor. `volatile` gives visibility and ordering but no atomicity, so `volatile int count; count++` still races. Guard each piece of shared state with one lock everywhere, and remember that calling a thread-safe class twice in a row still leaves a race between the two calls.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Builds on [Fundamentals](fundamentals.md).

## The core idea: shared mutable state

Threads in one process share the heap: instance fields, static fields, and every object reachable from them. Each thread gets its own stack, so local variables and parameters belong to that thread alone ([Fundamentals](fundamentals.md) covers the layout).

```java
class Hits {
    private int total;          // heap: every thread calling record() hits this one field

    void record(int n) {
        int doubled = n * 2;    // this thread's stack: nobody else can touch it
        total += doubled;       // shared and mutable, so it needs protection
    }
}
```

Trouble needs both conditions. State that's shared but never changes is safe, and so is state that changes but never leaves one thread. Code that reads or writes shared mutable state is a **critical section**. It has to run without another thread getting in halfway through.

For that state, concurrent code needs three guarantees:

| Guarantee | Meaning | Breaks when |
|---|---|---|
| Atomicity | A multi-step action happens all at once or not at all | `count++` is read, add, write, and another thread gets in between |
| Visibility | A write by one thread is seen by the others | A thread keeps looping on a stale `running` flag |
| Ordering | Other threads see writes in the order the code made them | The JIT or CPU reorders two writes, and a reader sees the second without the first |

`synchronized` gives all three. It gets atomicity through **mutual exclusion**: only one thread can be inside the critical section at a time. `volatile` gives visibility and ordering but not atomicity. `AtomicInteger` and its siblings give atomicity for a single variable. The ordering rules live in [the Java Memory Model](java-memory-model.md).

Two terms get mixed up. A **race condition** is a logic bug where the result depends on timing. A **data race** is narrower and defined by the JMM: two threads access the same field, at least one of them writes, and no happens-before edge orders the accesses. Data races usually cause race conditions, but a race condition can exist with no data race at all. Each call to a `ConcurrentHashMap` is properly synchronized, yet a check-then-act across two calls can still go wrong (see the last section).

Shared mutable state can be made safe by removing either half, or by guarding it:

- Don't share it. Keep it in locals, or confine it to one thread with `ThreadLocal`.
- Don't mutate it. Immutable objects need no locking ([Advanced topics](advanced.md)).
- Synchronize access. That's what the rest of this note is about.

## Why one core is enough for a race

`count++` isn't atomic. It compiles to three steps: read, add, write. The scheduler can preempt a thread between any two of them.

| Step | Thread A | Thread B | `count` |
|---|---|---|---|
| 1 | reads 5 | | 5 |
| 2 | preempted | | 5 |
| 3 | | reads 5, writes 6 | 6 |
| 4 | adds 1 to its stale 5, writes 6 | | **6** |

Two increments ran and the result is 6. All it took was interleaving, and any preemptive scheduler on one core can produce that.

## Lost updates in practice

Both runs below do 20,000 increments in total (two threads, 10,000 each). The only difference is `synchronized` on `incrementCounter()`:

```java
package com.threading;

public class RaceConditionExample {

    static void main() throws InterruptedException {
        counterWithNonVolatile();
        counterWithSynchronized();
    }

    private static void counterWithSynchronized() throws InterruptedException {
        CounterWithSynchronized c = new CounterWithSynchronized();
        Thread t1 = new Thread(() -> {
            for(int i = 1; i <=10000; i++) {
                c.incrementCounter();
            }
        });


        Thread t2 = new Thread(() -> {
            for(int i = 1; i <=10000; i++) {
                c.incrementCounter();
            }
        });

        t1.start();
        t2.start();


        t1.join();
        t2.join();

        IO.println("Counter = " + c.counter);
    }

    private static void counterWithNonVolatile() throws InterruptedException {
        Counter c = new Counter();
        Thread t1 = new Thread(() -> {
            for(int i = 1; i <=10000; i++) {
                c.incrementCounter();
            }
        });


        Thread t2 = new Thread(() -> {
            for(int i = 1; i <=10000; i++) {
                c.incrementCounter();
            }
        });

        t1.start();
        t2.start();


        t1.join();
        t2.join();

        IO.println("Counter = " + c.counter);
    }

}


class Counter {
    public int counter;

    public void incrementCounter() {
        counter++;
    }
}


class CounterWithSynchronized {
    public int counter;

    public synchronized void incrementCounter() {
        counter += 1;
    }
}
```

Six runs on JDK 25 printed:

```
Counter = 12047   Counter = 20000
Counter = 11615   Counter = 20000
Counter = 11686   Counter = 20000
Counter = 11675   Counter = 20000
Counter = 12309   Counter = 20000
Counter = 11374   Counter = 20000
```

The plain `Counter` lost roughly 40% of its updates, and a different amount each run. The synchronized one was exact every time.

- `counter++` and `counter += 1` compile to the same read-add-write. The fix comes from `synchronized`, not from the different syntax.
- Both threads call the same `CounterWithSynchronized` instance, so they contend for one monitor, `c`. Give each thread its own instance and the lock protects nothing.
- `main` reads `c.counter` with no lock, which is safe only because it does so after `join()`, and `join()` is a happens-before edge ([Thread communication](thread-communication.md)).
- Making the field `volatile` doesn't help, despite the method name `counterWithNonVolatile`. With `public volatile int counter;` the plain version still printed 11,716, 11,762 and 13,574. Visibility was never the problem here. The lost updates come from the read-add-write not being atomic.
- A run of the plain version can still come out at exactly 20,000, especially with smaller loop counts where one thread finishes before the other starts. So a passing run proves nothing.

To run it: the `package com.threading;` line means the file has to sit at `com/threading/RaceConditionExample.java`, launched with `java com/threading/RaceConditionExample.java`. The bare `static void main()` and `IO.println` come from Java 25's simpler main methods. The lock-free fix with `AtomicInteger` is in [Atomics and CAS](atomics-and-cas.md).

## synchronized

```java
public synchronized void inc() { count++; }   // locks this (or the Class object if static)

public void inc() {
    synchronized (lock) { count++; }          // locks only the critical part
}
```

- Every object has an intrinsic lock (monitor). The JVM releases it when the block exits, including on an exception, so it can't leak.
- It's reentrant: a thread already holding the monitor can enter again.
- A thread that takes the lock sees every write made by the last thread that released it. People tend to forget this visibility half.
- The lock belongs to the object, not the code. `static synchronized` locks `Account.class` and instance `synchronized` locks `this`. They don't exclude each other, so two such methods touching the same static field race. Guard that field with one shared lock, such as a `private static final Object`.
- Don't lock on `this` in a public class, on a `String` literal, or on a boxed `Integer`. Outside code can grab the same monitor. Use a `private final Object lock`.

## volatile

A write to a `volatile` field is visible to every later read of it. Without it, a thread can keep using a value it read earlier, forever, so `while (running)` may never exit.

This example runs the same spin loop twice, once on a `volatile` flag and once on a plain one:

```java
public class VolatileExample {
    public static volatile boolean volatileFlag = false;
    public static boolean nonVolatileFlag = false;

    static void main() throws InterruptedException {
        withVolatileVar();
        withoutVolatileVar();
    }

    private static void withoutVolatileVar() throws InterruptedException {
        Thread t1 = new Thread(() -> {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            nonVolatileFlag = true;
        });

        Thread t2 = new Thread(() -> {
            while(!nonVolatileFlag) {}
            System.out.println("Thread 2 completed!");
        });

        t1.start();
        t2.start();


        t1.join();
        t2.join();
    }

    private static void withVolatileVar() throws InterruptedException {
        Thread t1 = new Thread(() -> {
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
            volatileFlag = true;
        });

        Thread t2 = new Thread(() -> {
            while(!volatileFlag) {}
            System.out.println("Thread 2 completed!");
        });

        t1.start();
        t2.start();


        t1.join();
        t2.join();
    }


}
```

On JDK 25 (`java VolatileExample.java`, and the bare `static void main()` works because of Java 25's simpler main methods), it prints `Thread 2 completed!` once and then hangs:

- **`withVolatileVar`**: `t2` sees the flag about a second later and exits.
- **`withoutVolatileVar`**: `t2` spins forever, so `t2.join()` never returns and the program never exits. The empty loop runs hot, the JIT compiles it, and since nothing inside the loop writes `nonVolatileFlag`, the compiled code reads the flag once and loops on that value.

Run it with `java -Xint VolatileExample.java` (interpreter only, no JIT) and both halves finish. That shows the compiler causing the hang, not the CPU cache. The JMM doesn't promise the hang either, so the plain version is a data race that *may* hang. That's what makes this kind of bug pass tests and then fail in production. [The Java Memory Model](java-memory-model.md) note covers why.

A volatile write also publishes everything the same thread wrote before it:

```java
config = load();       // plain write
initialized = true;    // volatile write, written last
```

A reader that sees `initialized == true` is guaranteed to see the loaded `config`. Swap the two lines and that guarantee is gone. The rule behind this is happens-before, covered in the [Java Memory Model](java-memory-model.md) note.

## Atomicity

Reads and writes of `int`, `boolean` and references are atomic. Plain `long` and `double` aren't guaranteed atomic on 32-bit JVMs, so a reader can see half of one write. Declaring them `volatile` fixes that.

| Need | Use |
|---|---|
| One writer, many readers of a flag or reference | `volatile` |
| One counter or reference updated by many threads | `AtomicInteger`, `AtomicReference` |
| Several fields changed together, or check-then-act | `synchronized` or a lock |

## Thread-safe class, unsafe code

```java
if (cache.get(key) == null) cache.put(key, expensiveLoad(key));   // race
cache.computeIfAbsent(key, this::expensiveLoad);                  // atomic per key
```

`ConcurrentHashMap` makes each call atomic, not the sequence. The first line loads twice under concurrency, and different callers can get different instances. `computeIfAbsent` runs the loader at most once per key. Keep the loader fast, because it holds a bucket lock while it runs. And never modify the same map inside it: Java 9+ throws `IllegalStateException: Recursive update`.
