---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-11-05T00:00:00+08:00
title: "Database Replication: Why the Replica Lost Your Order"
tags: [system-design, distributed-systems, postgres, mysql]
categories: [System Design]
mermaid: true
---

You add a read replica to take load off the database. A user places an order, the page refreshes, and the order is gone. It isn't lost: the write landed on the leader, and the refresh read a replica that hadn't copied it yet. Four terms explain it:

- **Leader-follower replication**: one server, the leader (also called primary), takes every write. Followers (replicas) copy the leader's change log and replay it in order. Postgres calls the log the WAL (streaming replication); MySQL uses the binlog.
- **Asynchronous replication**: the default in Postgres and MySQL. The leader commits and answers the user before any follower has the change.
- **Replication lag**: the gap between a write committing on the leader and a follower having replayed it. Usually milliseconds, but heavy writes, or a slow query on the replica, can stretch it to seconds.
- **Synchronous replication**: the leader waits for a follower to confirm each write before answering. Nothing acknowledged is lost on failover, but every write gets slower.

**A read replica is not a live copy: with async replication it shows the database as it was a moment ago, so a user who writes and then reads from a replica can miss their own change.** So route each read by how stale it may be. I'll call that staleness routing. Product pages and feeds can be a second old, so they go to replicas. A user reading back what they just saved goes to the leader. Lagging replicas leave the read pool. Synchronous replication is for data you can't lose, like payments, and every write pays for it.

## The whiteboard next door

A teacher writes on the main whiteboard while helpers copy each line onto boards in other rooms. You add your name and walk next door. It isn't there yet. Main board = leader, other boards = followers replaying the change log, the wait = replication lag.

The Postgres manual describes the same gap. With streaming replication there is "a small delay between committing a transaction in the primary and the changes becoming visible in the standby", "typically under one second assuming the standby is powerful enough to keep up with the load". Under a second sounds harmless, but the redirect after a form post comes back in milliseconds.

## Following one order

Here's the order from the opening. The leader commits `#1042` and says OK straight away. The change is still on its way to the replica.

{{< mermaid >}}
sequenceDiagram
  participant A as App
  participant L as Leader
  participant R as Replica 1
  A->>L: INSERT order #1042
  L->>L: commit, write to WAL / binlog
  L-->>A: OK (async: no follower has it yet)
  L-)R: stream log record for #1042
  A->>R: SELECT order #1042
  R-->>A: not found (still replaying)
  R->>R: replay #1042
  A->>R: SELECT order #1042
  R-->>A: #1042
{{< /mermaid >}}

*Figure 1: The OK goes back before the log record reaches the replica. Any read that lands in between misses the order.*

In the animation, watch the number in each box: the latest order that copy holds.

{{< moving-diagram >}}
{
  "title": "Async replication: the replica runs behind",
  "subtitle": "write to the leader, read from Replica 1",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 250,
  "posterFrame": 95,
  "boxes": {
    "app":  [40, 170, 180, 230, "App"],
    "lead": [330, 40, 490, 100, "Leader", "#1041"],
    "rep1": [330, 290, 490, 350, "Replica 1", "#1041"],
    "rep2": [620, 170, 760, 230, "Replica 2", "#1041"]
  },
  "wires": [
    [[180,185],[330,80]],
    [[180,215],[330,320]],
    [[410,100],[410,290]],
    [[490,80],[690,170]]
  ],
  "moves": [
    { "start": 8,   "end": 28,  "path": [[180,185],[330,80]], "color": "primary", "label": "write #1042" },
    { "start": 33,  "end": 50,  "path": [[330,80],[180,185]], "color": "primary", "label": "OK" },
    { "start": 33,  "end": 125, "path": [[410,100],[410,290]], "color": "secondary", "label": "log" },
    { "start": 33,  "end": 140, "path": [[490,80],[690,170]], "color": "secondary", "label": "log" },
    { "start": 58,  "end": 75,  "path": [[180,215],[330,320]], "color": "primary", "label": "read #1042" },
    { "start": 78,  "end": 92,  "path": [[330,320],[180,215]], "color": "secondary", "label": "not found" },
    { "start": 140, "end": 157, "path": [[180,215],[330,320]], "color": "primary", "label": "read #1042" },
    { "start": 160, "end": 174, "path": [[330,320],[180,215]], "color": "primary", "label": "#1042" }
  ],
  "resize": [
    { "box": "lead", "start": 26,  "end": 28,  "to": [330, 40, 490, 100], "sub": "#1042" },
    { "box": "rep1", "start": 123, "end": 125, "to": [330, 290, 490, 350], "sub": "#1042" },
    { "box": "rep2", "start": 138, "end": 140, "to": [620, 170, 760, 230], "sub": "#1042" }
  ],
  "tags": [
    { "start": 33,  "end": 55,  "x": 470, "y": 200, "text": "lag 0.0 s", "color": "secondary" },
    { "start": 55,  "end": 80,  "x": 470, "y": 200, "text": "lag 0.3 s", "color": "secondary" },
    { "start": 80,  "end": 105, "x": 470, "y": 200, "text": "lag 0.6 s", "color": "secondary" },
    { "start": 105, "end": 125, "x": 470, "y": 200, "text": "lag 0.9 s", "color": "secondary" },
    { "start": 125, "end": 250, "x": 470, "y": 200, "text": "caught up", "color": "primary" },
    { "start": 92,  "end": 138, "x": 110, "y": 260, "text": "✕ not found", "color": "secondary" },
    { "start": 174, "end": 250, "x": 110, "y": 260, "text": "✓ #1042", "color": "primary" }
  ],
  "captions": [
    { "start": 0,   "end": 30,  "text": "the user writes order #1042 to the leader", "color": "primary" },
    { "start": 30,  "end": 58,  "text": "the leader says OK at once; the log is still in transit", "color": "primary" },
    { "start": 58,  "end": 125, "text": "the read hits Replica 1, which doesn't have #1042 yet", "color": "secondary" },
    { "start": 125, "end": 180, "text": "Replica 1 replays the log; the same read now works", "color": "primary" },
    { "start": 180, "end": 999, "text": "Replicas run a moment behind: read your own writes from the leader", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

*Figure 2: The OK reaches the app long before the log reaches Replica 1, so the first read comes back empty. Nothing is lost. The second read, after replay, finds the order.*

The lag counter is illustrative and the clip is slowed down.[^lag] In a healthy setup that 0.9 s is usually a few milliseconds, but the order is the same: acknowledged first, copied second.

## Routing reads by staleness

Staleness routing starts with one question for each read: how old may this answer be?

- **Can be a second or more old**: product pages, feeds, search results, yesterday's sales report. Send these to replicas; that's usually where the read load is. The [vertical vs horizontal scaling](../vertical-vs-horizontal-scaling/) note calls read replicas the first step once the shared database becomes the limit.
- **Must include the user's own change**: the order page right after checkout, a profile right after an edit. This is read-your-writes. The simple fix: after a user saves, read that user's data from the leader for a few seconds. A "last write at" timestamp in the session is enough to route on.
- **Must be current for everyone**: an inventory check before payment, a balance before a withdrawal. Always the leader.

The leader-read window has to be longer than your worst normal lag, so measure lag first. A tighter Postgres option is to remember the WAL position of the user's write and only use a replica whose `pg_last_wal_replay_lsn()` has passed it. That's more code, so I'd start with the timer.

The calculator covers both costs: replicas needed once some reads go to the leader, and what synchronous replication adds to each write.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Your traffic",
      "inputs": [
        { "id": "reads", "label": "Reads per second", "default": 20000, "step": 1000 },
        { "id": "leaderShare", "label": "Reads that must go to the leader", "unit": "%", "default": 5, "step": 1 },
        { "id": "replicaCap", "label": "Reads one replica can serve", "unit": "per s", "default": 5000, "step": 500 },
        { "id": "commitMs", "label": "Local commit on the leader", "unit": "ms", "default": 2, "step": 0.5 },
        { "id": "rttMs", "label": "Round trip to the synchronous follower", "unit": "ms", "default": 0.5, "step": 0.5 }
      ]
    },
    {
      "title": "What it costs",
      "outputs": [
        { "id": "leaderReads", "label": "Reads on the leader (per s)", "formula": "reads * Math.min(100, Math.max(0, leaderShare)) / 100", "format": "number" },
        { "id": "replicaReads", "label": "Reads on replicas (per s)", "formula": "reads * (1 - Math.min(100, Math.max(0, leaderShare)) / 100)", "format": "number" },
        { "id": "replicas", "label": "Replicas needed", "formula": "Math.ceil(reads * (1 - Math.min(100, Math.max(0, leaderShare)) / 100) / Math.max(1, replicaCap))", "format": "number" },
        { "id": "asyncMs", "label": "Async write latency (ms)", "formula": "commitMs", "format": "number" },
        { "id": "syncMs", "label": "Sync write latency, at least (ms)", "formula": "commitMs + rttMs", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

*Figure 3: Pinning 5% of reads to the leader costs it 1,000 reads a second. Set the round trip to 150 and watch a synchronous write go from 2.5 ms to 152 ms.*

The model splits reads evenly across replicas and counts only the round trip as sync's extra cost (Postgres: "the minimum wait time is the round-trip time between primary and standby"), so the sync figure is a floor. By hand with the defaults: 20,000 × 5% = 1,000 leader reads, 19,000 / 5,000 = 3.8, so 4 replicas, and 2 + 0.5 = 2.5 ms per synchronous write. A follower in another region (~150 ms round trip, per the [latency numbers](../latency-numbers/) note) makes each write wait ~152 ms.

## Failover: where async lag turns into data loss

Stale reads are annoying; failover is where async lag costs data. When the leader dies and a follower is promoted, writes the old leader acknowledged but hadn't shipped aren't on the new one. Postgres puts it plainly: "The amount of data loss is proportional to the replication delay at the time of failover."

{{< moving-diagram >}}
{
  "title": "Async failover strands writes",
  "subtitle": "leader acknowledged #1043 and #1044, follower only has #1042",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 220,
  "posterFrame": 150,
  "boxes": {
    "app":  [40, 170, 180, 230, "App"],
    "east": [330, 40, 490, 100, "Leader (East)", "#1042"],
    "west": [330, 290, 490, 350, "Follower (West)", "#1042"]
  },
  "wires": [
    [[180,185],[330,80]],
    [[180,215],[330,320]],
    [[410,100],[410,290]]
  ],
  "moves": [
    { "start": 8,   "end": 26,  "path": [[180,185],[330,80]], "color": "primary", "label": "#1043" },
    { "start": 30,  "end": 48,  "path": [[180,185],[330,80]], "color": "primary", "label": "#1044" },
    { "start": 30,  "end": 75,  "path": [[410,100],[410,180]], "color": "secondary", "label": "log #1043" },
    { "start": 120, "end": 140, "path": [[180,215],[330,320]], "color": "primary", "label": "new writes" }
  ],
  "resize": [
    { "box": "east", "start": 24,  "end": 26,  "to": [330, 40, 490, 100], "sub": "#1043" },
    { "box": "east", "start": 46,  "end": 48,  "to": [330, 40, 490, 100], "sub": "#1044" },
    { "box": "west", "start": 95,  "end": 100, "to": [330, 290, 490, 350], "sub": "#1042 · promoted" }
  ],
  "tags": [
    { "start": 48,  "end": 140, "x": 600, "y": 70,  "text": "acked: #1043, #1044", "color": "primary" },
    { "start": 75,  "end": 220, "x": 470, "y": 200, "text": "✕ link down", "color": "secondary" },
    { "start": 140, "end": 220, "x": 620, "y": 70,  "text": "#1043, #1044 only here", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 50,  "text": "the leader acknowledges two orders", "color": "primary" },
    { "start": 50,  "end": 95,  "text": "the link drops before the log reaches the follower", "color": "secondary" },
    { "start": 95,  "end": 140, "text": "the follower is promoted and takes new writes", "color": "primary" },
    { "start": 140, "end": 999, "text": "two acknowledged orders now exist only on the old leader", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

*Figure 4: The orders were acknowledged, so the users think they're saved. After promotion they exist only on the old leader, and someone has to merge them back by hand.*

That's what happened to GitHub on 21 October 2018. Connectivity between a network hub and their primary US East Coast data center was lost and "restored in 43 seconds". In that window their failover tool, orchestrator, had started moving MySQL leadership, and the West Coast nodes began "failing over clusters to direct writes to the US West Coast data center". The East Coast leaders held a short stretch of writes that "had not been replicated to the US West Coast facility". GitHub chose to "prioritize data integrity over site usability and time to recovery", and the incident "resulted in degraded service for 24 hours and 11 minutes."

So 43 seconds of network trouble cost about a day. The lag was small; the cost was two leaders with different histories, reconciled by hand.

## The case for sending every read to a replica

The strongest view against staleness routing: lag is usually milliseconds, and routing reads by type adds code paths, session state and a leader that can still get overloaded. So send every read to replicas and accept a rare stale page.

For most read traffic, that's right. A feed a second old is fine, and one read pool is simpler to run. It breaks on the pages users check right after saving, like checkout and profile edits, because those reads arrive within milliseconds of the write. The fix is cheap too. In my experience those pages are a small share of traffic, but measure that share before you rely on it.

The opposite view, "make it all synchronous", fixes data loss, not stale reads. By default Postgres's synchronous mode waits for the standby to flush the change to disk, not replay it, so a read there can still miss it.[^apply]

## Failure modes of staleness routing

Staleness routing assumes the lag stays small and that you'll notice when it doesn't. Here's how each part fails:

- **Lag spikes past the leader-read window.** A batch job or write burst puts replicas seconds behind, and a 2-second window starts handing out stale reads. A long query on a Postgres standby can pause replay too, up to `max_standby_streaming_delay`, after which Postgres cancels the query.
- **The lag metric lies.** MySQL's `Seconds_Behind_Source` compares the replica's applier with its receiver, so on a slow network it "often shows a value of 0, even if the replication receiver thread is late". The manual's verdict: "this column is useful only for fast networks". On Postgres, `pg_stat_replication.replay_lag` reverts to NULL on an idle, caught-up system, so treat NULL as "no data", not as a fault.
- **Reads bounce between replicas.** If a user's requests hit replicas with different lag, a page can show the order and then lose it on refresh. Pinning a user to one replica helps.
- **The leader drowns in pinned reads.** If most traffic writes and then reads, the window sends most reads back to the leader and the replicas stop helping.
- **Sync replication stalls writes.** Commits "may never be completed if any one of the synchronous standbys should crash", unless you list spare standbys. It suits a payments table better than a whole database.

## What to measure

- **Replication lag per replica**: `replay_lag` in `pg_stat_replication` (Postgres), `Seconds_Behind_Source` in `SHOW REPLICA STATUS` (MySQL). Alert on it, and pull a replica from the read pool when it passes your leader-read window.
- **The p99 of that lag, not the average.** The window has to cover the bad minutes.
- **Leader read share**: reads sent to the leader by the window. If it climbs, the replicas are doing less than you think.
- **Write latency before and after** turning on synchronous replication, especially cross-region.

If queries are slow on the leader too, check the [indexes](../database-indexes/) first. A replica copies the slow query along with the data.

## The takeaway

A replica shows the database as it was a moment ago, and staleness routing plans for that. Ask of each read how old the answer may be. Send the ones that can be a little old to replicas, and a user's reads to the leader for a few seconds after they save. Watch p99 lag and pull a replica from the pool once it falls behind your window. Use synchronous replication only where losing an acknowledged write would really hurt, and expect each write there to wait one round trip.

## References

**Incident reports**
- [October 21 post-incident analysis](https://github.blog/2018-10-30-oct21-post-incident-analysis/), GitHub Engineering, 30 October 2018.

**Documentation**
- [Log-Shipping Standby Servers](https://www.postgresql.org/docs/current/warm-standby.html), PostgreSQL manual: streaming replication, synchronous replication and its cost.
- [Hot Standby](https://www.postgresql.org/docs/current/hot-standby.html), PostgreSQL manual: reads on a standby, "eventually consistent" data, and query conflicts.
- [The Cumulative Statistics System](https://www.postgresql.org/docs/current/monitoring-stats.html), PostgreSQL manual: the `pg_stat_replication` lag columns.
- [Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html), MySQL 8.4 manual. "Replication is asynchronous by default."
- [SHOW REPLICA STATUS Statement](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html), MySQL 8.4 manual: what `Seconds_Behind_Source` measures and when it misleads.

[^lag]: The 0.9 s in the animation and the default calculator values are illustrative, not measured. Use your own lag and capacity numbers.
[^apply]: Postgres has a stricter level, `synchronous_commit = remote_apply`, which waits for the standby to apply the change. The manual's description of `replay_lag` mentions it as the delay that level adds to each commit.
