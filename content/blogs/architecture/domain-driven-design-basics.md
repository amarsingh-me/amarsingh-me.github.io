---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-14
title: Domain-Driven Design Basics
tags: [ddd, domain-driven-design, system-design, microservices]
categories: [Distributed Systems]
---

Domain-Driven Design rests on three load-bearing concepts: the bounded context, the ubiquitous language, and the aggregate.

A **bounded context** is a boundary within which a model is valid and internally consistent. The same term can mean something different depending on which context it's used in — "Customer" in a Billing context might carry billing address and payment methods, while "Customer" in a Support context carries ticket history and support tier. Rather than forcing one shared "Customer" model across the whole system, DDD accepts that each context gets its own model of the term, valid only within its own boundary. Bounded contexts are also a common lens for drawing microservice boundaries — see [Microservices Architecture Fundamentals]({{< ref "../architecture/microservices-fundamentals.md" >}}).

The **ubiquitous language** is a vocabulary shared between engineers and domain experts, and — critically — reflected directly in code: class names, method names, module names. The point is to stop a term from being precise in conversation with a domain expert but then getting lost or renamed once it hits the codebase; the same word should mean the same thing whether you're in a requirements meeting or reading a class definition.

An **aggregate** is a cluster of related objects treated as a single consistency boundary. Changes to anything inside the aggregate go through one entry point — the **aggregate root** — which is the only object allowed to enforce the aggregate's invariants. Nothing outside the aggregate is allowed to reach in and modify an internal object directly; it has to go through the root, which is what keeps the aggregate's invariants actually enforceable.
