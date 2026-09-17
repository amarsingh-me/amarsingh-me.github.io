---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-02
title: "WebSockets in Java: Threading, Scaling, and Virtual Threads"
tags: [java, websockets, threading, virtual-threads, concurrency]
categories: [Java]
---

WebSockets give a persistent, full-duplex connection so a server can push data anytime (unlike request/response HTTP). Java servers hold thousands of these open cheaply via an event-loop (small selector thread pool + worker thread pool), but bursts of blocking work saturate the fixed worker pool. Virtual threads (Java 21+) make thread-per-task cheap again at scale by unmounting from real "carrier" threads whenever they block — but pinning (inside `synchronized`, pre-Java 24) defeats that benefit.

## WebSockets vs HTTP

Plain HTTP is one-shot: client asks, server answers, done. That's bad for chat/live apps because the *server* needs to push data unprompted. A WebSocket starts as an HTTP request that "upgrades" (`Connection: Upgrade`) into a persistent TCP connection both sides can write to at any time — no polling, no per-message request overhead, and the server can initiate messages (which plain HTTP can't do).

Concrete contrast for a chat app:
- **HTTP polling**: browser does `GET /messages` every N seconds regardless of whether anything happened; sending a message is a separate `POST`. Wasteful and laggy (you only see new messages on your next poll).
- **WebSocket**: one upgrade handshake, then messages flow instantly in both directions over the same open connection.

## How Java servers hold thousands of connections open

Two strategies:
1. **Blocking I/O (old-school, thread-per-connection)**: one OS thread per open connection, parked in `socket.read()` doing nothing until data arrives. Simple, but each Java thread costs ~1MB stack + real OS scheduling overhead — 10,000 open connections ≈ 10,000 idle threads ≈ ~10GB RAM. This is the classic **C10K problem**.
2. **Non-blocking I/O / event loop (modern default — Tomcat/Jetty/Netty)**: a small number of "selector" threads (matching CPU core count) use OS-level multiplexing (epoll) to watch thousands of sockets at once and get woken only when a socket actually has data. The real work (running `onMessage`) is then handed off to a separate **worker thread pool**; threads aren't dedicated to a connection, they're shared and only busy when there's real work.

## What happens under a sudden surge (e.g. 10,000 concurrent requests)

Two separate bottlenecks:
- **Accepting connections**: cheap with an event-loop server — mostly just registering a socket with the selector, so this scales well even under a burst.
- **Processing the work**: bounded by the worker pool size (e.g. 200 threads). If 10,000 messages arrive at once and each handler is fast, the queue drains quickly. But if handlers **block** (DB calls, slow network calls to other services), those pool threads stay tied up, the queue backs up hard, and:
  - unbounded queue → memory balloons, risk of OOM
  - bounded queue → once full, new work gets rejected outright or times out

  Net: you don't get a graceful slowdown, you hit a wall determined by how many platform threads you can afford to keep alive (each one costs real memory).

## Virtual threads (Java 21+, Project Loom) and how they change this

Virtual threads decouple "a thread as a unit of concurrency in code" from "a thread as an OS resource." They look and behave like normal `Thread`s in code, but run on top of a small pool of real OS threads called **carrier threads**. When code on a virtual thread hits a blocking call (socket read, JDBC call, `Thread.sleep`), the JVM **unmounts** it from its carrier thread, freeing that carrier to run some other virtual thread; when the blocking op completes, the virtual thread **remounts** onto any free carrier and continues. A blocked virtual thread costs almost nothing (a few hundred bytes on heap, no dedicated OS stack), so you can have millions of them.

Effect on the surge scenario: spin up one virtual thread per task/connection freely. Each blocks individually on its DB call, but that doesn't tie up a scarce OS thread — it just parks cheaply, and the small set of carrier threads keeps getting reused by whichever virtual threads are ready to run. The old thread-per-connection model (simple, blocking, easy-to-read code — no callbacks/reactive gymnastics) becomes viable again at scale.

For Java WebSockets concretely: Tomcat 10.1+/Jetty 12+ can be configured to run request/message handling on a virtual-thread-per-task executor, so each `onMessage` call gets its own (cheap) virtual thread instead of borrowing from a small fixed pool.

## The catch: pinning

Pinning is when a virtual thread blocks but **can't** unmount — it holds its carrier thread the whole time, just like an old platform thread. Enough pinned virtual threads at once and you're back to carrier-thread starvation.

Causes:
- **Inside a `synchronized` block/method**: blocking while holding a `synchronized` lock pins the carrier for the whole block. Fixed in **Java 24 (JEP 491)** — but a real trap on Java 21-23, especially since older WebSocket frameworks or shared-state code (e.g. a `synchronized Map<String, Session>` tracking connected clients) commonly use `synchronized` instead of `java.util.concurrent.locks.ReentrantLock`.
- **Native/JNI code**: the JVM can't see into native calls, so it can't unmount around them.

Mitigations: swap `synchronized` for `ReentrantLock` in hot paths, upgrade to Java 24+ where possible, detect pinning via JFR events or `-Djdk.tracePinnedThreads=full`.

Two more honest caveats:
- Virtual threads help **I/O-bound** concurrency only — zero benefit for CPU-bound handler work (still limited by core count).
- Don't **pool** virtual threads (no `Executors.newFixedThreadPool` equivalent) — the model is create-cheaply-per-task, not reuse; pooling them is an anti-pattern carried over from platform-thread habits.
