---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-30
title: CQRS - Command Query Responsibility Segregation
tags: [cqrs, event-sourcing, kafka, event-driven-architecture, distributed-systems]
categories: [Distributed Systems]
---

CQRS splits the model used to **write** state from the model used to **read** it — a separate schema/structure for queries, kept in sync with the write side asynchronously. It's easy to conflate this with a read replica or a cache, but those just copy the *same* shape for scale; CQRS earns its complexity when the read side needs a genuinely **different shape** than the write side — a normalized, invariant-enforcing write model (an `Order` aggregate, see [Domain-Driven Design Basics](../architecture/domain-driven-design-basics.md)) versus a denormalized, joined read model (`OrderSummaryView` for a dashboard). Balanced read/write load with matching shapes doesn't justify CQRS — read replicas are simpler and solve that. Diverging shapes do, regardless of load.

**Keeping the two in sync** is where it lives or dies. The naive approach — write to the write-model table, then write to the read-model table (or publish to Kafka) in a second step — has a gap: if the second write fails after the first commits, the models silently drift with nothing to flag it. This is the **dual-write problem**, and it applies equally to "DB then DB" and "DB then Kafka publish."

The standard fix is the **transactional outbox pattern**: write the domain event (e.g. `OrderPlaced`) into an `outbox` table in the *same DB transaction* as the write-model change, so both commit or neither does. A separate process — Debezium CDC or a poller — reads the outbox and publishes to Kafka; that publish step can fail and retry independently, because the event is already durably committed. Consumers ("projectors") subscribe to the topic and update the read model. See [Apache Kafka Concepts](../kafka/apache-kafka-concepts/index.md) for how Kafka's delivery guarantees work underneath this.

**Event sourcing is a separate, optional idea** people often bundle with CQRS. CQRS just needs *some* reliable way to publish change events — the outbox above is enough. Event sourcing goes further: the event log itself becomes the source of truth, and current state is derived by replaying it, rather than being stored directly. You can do CQRS without event sourcing (normal write-model table + outbox), and you can event-source a system with only one model. They pair well together, but neither implies the other.

**Read-your-own-writes** is the concrete pain the async gap causes: a user submits something, gets routed to a page reading from the read model, and the projector hasn't caught up — so they see stale or missing data right after their own action. The fix depends on what the read actually needs. If the write already has all the data the page needs (an order confirmation page right after "place order" — ID, items, total), serve it straight from the write side or the command response, skipping the read model entirely for that call. If the read needs something only the read model computes (a cross-service aggregate, a join), either have the read API wait — bounded, with a timeout — until it's caught up to the write's version/offset, or, for low-stakes views like a dashboard, just show it as-is and accept the lag.

**Rebuilding the read model** comes up when the projection logic had a bug, a new read shape is needed, or the read store is lost. Whether you can replay depends on what's retained: full event sourcing keeps the log forever by design, so rebuild is just replay-from-zero into a fresh store. Outbox-to-Kafka without event sourcing relies on topic retention — a 7-day retention window won't give you a year of history. Log compaction keyed by aggregate ID keeps the *latest* value per key indefinitely, which covers current-state rebuilds even without full history; otherwise, backfill directly from the write-model DB and only replay Kafka for the recent gap. Either way, rebuild into a new table and swap once caught up, rather than replaying against the live one.

**Projectors have to be idempotent**, because replay is just redelivery at scale — the same at-least-once guarantee covered in [Event-Driven Architecture Patterns](../architecture/event-driven-patterns.md). A projector doing `readModel.total += event.amount` breaks on any duplicate delivery, replay included, silently double-counting. The fix is either tracking which event IDs have already been applied and skipping repeats, or making the operation itself idempotent — recomputing the total as a `SUM(...)` upsert instead of incrementing, so applying the same event twice produces the same result as applying it once.
