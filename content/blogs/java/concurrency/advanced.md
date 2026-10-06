---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-07T00:00:00+08:00
title: "Java Concurrency: ThreadLocal, Structured Concurrency, Immutability, Actors"
tags: [java, concurrency, threading, virtual-threads, reactive-programming]
categories: [Java]
---

`ThreadLocal` gives each thread its own copy of a value. It's handy for request context, but thread pools reuse threads, so values leak into the next request unless you call `remove()`. With millions of virtual threads, per-thread copies get expensive, and Java 25's `ScopedValue` is the immutable, bounded-lifetime replacement. Structured concurrency (`StructuredTaskScope`, still in preview) treats a group of subtasks as one unit: they finish, fail, or get cancelled together. Immutable objects need no locking at all. The actor model avoids shared state by giving each actor a private mailbox that it processes one message at a time. Reactive programming handles streams without blocking and with backpressure, on a few event-loop threads.

Part of the [Java Concurrency Roadmap](java-concurrency.md). Virtual threads themselves are covered in [WebSockets, threading and virtual threads](../websockets-threading-virtual-threads.md).

## ThreadLocal

```java
private static final ThreadLocal<RequestContext> CTX = new ThreadLocal<>();

try {
    CTX.set(ctx);
    handle(request);
} finally {
    CTX.remove();        // without this, the next request on this pooled thread sees ctx
}
```

Spring's `SecurityContextHolder`, the transaction synchronization manager, and SLF4J's `MDC` are all built on it. Gotchas:

- **Leaks between requests** when you skip `remove()`. User A's security context then shows up in user B's request.
- **Memory and classloader leaks** in app servers. The `ThreadLocalMap` entry holds the value strongly, so a redeployed webapp's classes can stay pinned in memory.
- `InheritableThreadLocal` copies the value only when a thread is *created*. Pooled threads are created once, so they keep whatever value they inherited first.

## ScopedValue (Java 25)

```java
static final ScopedValue<User> USER = ScopedValue.newInstance();
ScopedValue.where(USER, user).run(() -> handle(request));   // USER.get() works inside, gone after
```

The binding is immutable and lasts only for that call, so it can't leak. Child threads in a structured scope inherit it cheaply.

## Structured concurrency

```java
try (var scope = StructuredTaskScope.open()) {         // JDK 25 preview API
    Subtask<User>        user   = scope.fork(() -> findUser(id));
    Subtask<List<Order>> orders = scope.fork(() -> fetchOrders(id));
    scope.join();            // throws if any subtask failed; the others are cancelled
    return new Page(user.get(), orders.get());
}
```

Compare this with two raw `CompletableFuture`s. There, if `findUser` fails, `fetchOrders` keeps running with nobody waiting for its result, and if the caller is interrupted, neither subtask notices. A scope ties the subtasks' lifetime to the code block, which rules out orphaned threads, and thread dumps show them as a parent-child tree. It needs `--enable-preview` and pairs naturally with virtual threads.

## Immutability

An immutable object is thread-safe by construction, and its `final` fields make it safe to publish ([JMM](java-memory-model.md)). The recipe: `private final` fields, no setters, no `this` escaping from the constructor, and defensive copies of mutable inputs.

```java
record Order(String id, List<Item> items) {
    Order { items = List.copyOf(items); }   // records are only shallowly immutable
}
```

When state has to change, build a new immutable snapshot and swap it in through an `AtomicReference`. Readers never need a lock.

## Actor model

Each actor owns its state and a mailbox, handles one message at a time, and talks to other actors only by sending messages. With no shared memory there are no locks, and a failure is contained in a single actor. Erlang and Akka work this way. Akka moved to a commercial license in 2022, and Apache Pekko is the open-source fork. A Kafka partition with one consumer follows the same single-writer idea ([Kafka concepts](../../kafka/apache-kafka-concepts/index.md)). The trade-offs are request/response flows that are clumsy to write, mailboxes that can overflow, and failures that are harder to trace.

## Reactive programming basics

Reactive Streams (`java.util.concurrent.Flow` since Java 9) defines a `Publisher` and a `Subscriber`. The subscriber calls `request(n)` to pull only as much as it can handle, and that's the backpressure. Project Reactor's `Mono` and `Flux` implement it, and WebFlux runs them on a few event-loop threads that must never block. Virtual threads now handle most of the "many concurrent I/O calls" cases with ordinary blocking code. Reactive still makes sense for real streaming and backpressure. More in [WebFlux and reactive programming](../../spring/webflux-reactive-programming.md).
