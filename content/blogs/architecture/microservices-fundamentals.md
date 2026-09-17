---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-14
title: Microservices Architecture Fundamentals
tags: [microservices, distributed-systems, system-design]
categories: [Distributed Systems]
---

Microservices are services bounded by business capability, each owning its own data store, independently deployable and independently scalable. The hard parts are the boundaries between them: what talks sync vs. async, how consistency is kept without distributed transactions, and how failures in one service don't cascade into all of them.

## Core definition

Services bounded by business capability, each owning its own data store, independently deployable and independently scalable. "Database-per-service" — no service reaches directly into another's database — is the load-bearing rule that makes independent deployability actually hold; a shared DB across services re-couples them even if the code is split.
