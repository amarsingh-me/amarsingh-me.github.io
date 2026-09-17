---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-14
title: Event-Driven Architecture Patterns
tags: [event-driven-architecture, microservices, messaging, kafka]
categories: [Distributed Systems]
---

Event-driven systems are built around pub-sub: producers publish events without knowing who — or whether anyone — consumes them. That lack of a direct dependency between producer and consumer is what decouples services from each other in the first place.

Two coordination styles sit on top of that same pub-sub foundation. **Choreography** has each service react to events independently, with no central coordinator directing the flow — good for loose coupling, but harder to trace an end-to-end flow since the logic is spread across every participant. **Orchestration** puts a central process in charge, explicitly sequencing calls to the other services — easier to trace and reason about as a single flow, but that orchestrator itself becomes a coupling point that every participant now depends on.

Whichever style is used, consumers need to be **idempotent**. Most message brokers, Kafka included, deliver **at-least-once** by default, which means the same event can arrive — and get processed — more than once. If handling an event isn't safe to repeat, a duplicate delivery becomes a bug, not just an inefficiency. See [Apache Kafka Concepts]({{< ref "../kafka/apache-kafka-concepts/index.md" >}}) for how Kafka's delivery guarantees work under the hood.
