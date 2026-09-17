---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-14
title: Spring WebFlux and Reactive Programming
tags: [spring-boot, spring, reactive-programming, java]
categories: [Java]
---

WebFlux is Spring's reactive stack, built on Project Reactor — lazy, backpressure-aware streams (`Mono`/`Flux`) running on a small event-loop of threads (Netty) instead of one thread blocked per request. It's a concurrency model, not an architecture style — reactive programming and microservices are separate concepts.

- **`Mono`** = 0–1 result, **`Flux`** = 0–N results — the two core reactive types from Project Reactor.
- Reactive streams are **lazy** — nothing executes until something subscribes.
- **Backpressure** — a slow consumer can signal a fast producer to slow down, instead of being overwhelmed or dropping data.
- Runs on an **event-loop model (Netty)**: a small, fixed number of threads handle many concurrent requests via non-blocking I/O, instead of one thread blocked per request waiting on I/O.
- This is precisely what fixes the classic "thread pool exhaustion under load" failure mode — see [Spring Boot Core Concepts]({{< ref "../spring/core-concepts.md" >}}) (diagnosing a slow-under-load REST endpoint). Blocking calls (JDBC, blocking HTTP) tie up a scarce worker thread for their duration under the traditional Spring MVC/Tomcat model; WebFlux threads never sit idle waiting on I/O.
- **Reactive programming ≠ microservices.** WebFlux is an in-process concurrency model (how one service handles concurrent requests internally); microservices is a distributed-systems architecture style (how many independent services are organized). Don't conflate the two in an interview answer.
