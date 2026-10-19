---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-20T00:00:00+08:00
title: Vertical vs Horizontal Scaling
tags: [system-design, distributed-systems, performance]
categories: [System Design]
mermaid: true
---

When traffic outgrows one server, you have two ways out:

- **Vertical scaling (scale up)**: give the same machine more CPU, more RAM and a faster disk. No code changes.
- **Horizontal scaling (scale out)**: add more machines and put a load balancer in front. Capacity grows roughly with the number of machines, and losing one is survivable.

What that means in practice: vertical scaling is the fast, cheap fix, but every machine has a top size and it's still one machine, so when it dies you're down. Horizontal scaling has no top size and survives failures, but it only works for stateless servers. A session held in one server's memory breaks it, so that state has to move to Redis, a signed token or the database. Either way, the shared database is usually what stops you next: read replicas come first, sharding much later.

## The supermarket

Vertical scaling is hiring a faster cashier. It helps, until nobody faster exists. Horizontal scaling is opening more counters. Now someone has to point customers to a free counter, and that's the load balancer. And every counter still sells from the same stock room. That's your database.

## Scaling up

The appeal is that nothing changes. Same code, same deploy, same single database connection string. You stop the VM, pick a bigger instance type, and start it again. On most clouds that resize means a restart, so even scaling up costs a few minutes of downtime unless something else takes the traffic meanwhile.

It goes further than people expect. Stack Overflow famously served huge traffic from a handful of big servers for years. Today's largest cloud instances have hundreds of vCPUs and terabytes of RAM, which is more than most products will ever need for their app tier.

{{< moving-diagram >}}
{
  "title": "Vertical scaling",
  "subtitle": "A bigger machine, until there is no bigger one",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 190,
  "boxes": {
    "client": [30, 140, 190, 200, "Client"],
    "s2":     [290, 145, 420, 195, "Server: 2 vCPU"],
    "s4":     [455, 130, 605, 210, "Server: 4 vCPU"],
    "s8":     [635, 110, 790, 230, "Server: 8 vCPU"]
  },
  "wires": [
    [[190,170],[290,170]],
    [[110,140],[110,70],[530,70],[530,130]],
    [[110,200],[110,280],[712,280],[712,230]]
  ],
  "moves": [
    { "start": 5,   "end": 20,  "path": [[190,170],[290,170]], "color": "primary", "label": "req" },
    { "start": 24,  "end": 39,  "path": [[190,170],[290,170]], "color": "primary", "label": "req" },
    { "start": 43,  "end": 58,  "path": [[190,170],[290,170]], "color": "primary", "label": "req" },
    { "start": 72,  "end": 90,  "path": [[110,140],[110,70],[530,70],[530,130]], "color": "primary", "label": "req" },
    { "start": 94,  "end": 112, "path": [[110,140],[110,70],[530,70],[530,130]], "color": "primary", "label": "req" },
    { "start": 124, "end": 144, "path": [[110,200],[110,280],[712,280],[712,230]], "color": "secondary", "label": "req" },
    { "start": 148, "end": 168, "path": [[110,200],[110,280],[712,280],[712,230]], "color": "secondary", "label": "req" }
  ],
  "captions": [
    { "start": 0,   "end": 62,  "text": "2 vCPU: traffic grows, load climbs to 90%", "color": "primary" },
    { "start": 62,  "end": 120, "text": "scale up to 4 vCPU: load drops to 45%, then climbs again", "color": "primary" },
    { "start": 120, "end": 170, "text": "8 vCPU: load hits 100%, and this is the max size", "color": "secondary" },
    { "start": 170, "end": 999, "text": "vertical = bigger machine, until there is no bigger one", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

Three things end the road:

1. **The ceiling.** The biggest box exists, and near the top of the range the price per core climbs because you're paying for specialist hardware.
2. **The software.** More cores only help code that uses them. A single-threaded Node.js process or a Python app held back by the GIL won't go faster on 64 cores than on 8. Neither will a hot lock that every request takes.
3. **The single point of failure.** One machine means one kernel panic, one bad disk or one botched deploy away from a full outage. A bigger box fails just as completely as a small one.

## Scaling out

With several servers behind a load balancer, capacity grows roughly with the number of machines. The load balancer spreads requests (round-robin, or least-connections if requests vary a lot in cost), and it runs health checks so a dead server stops getting traffic.

{{< mermaid >}}
sequenceDiagram
  participant C as Client
  participant LB as Load balancer
  participant S1 as Server 1
  participant S2 as Server 2
  participant S3 as Server 3
  C->>LB: request
  LB->>S1: round-robin
  C->>LB: request
  LB->>S2: round-robin
  LB->>S2: health check
  Note over S2: no answer, marked down
  C->>LB: request
  LB->>S3: skips Server 2
  C->>LB: request
  LB->>S1: skips Server 2
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Horizontal scaling",
  "subtitle": "More machines: lose one, traffic keeps flowing",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 210,
  "boxes": {
    "client": [20, 150, 160, 190, "Client"],
    "lb":     [230, 150, 390, 190, "Load balancer"],
    "s1":     [560, 50, 740, 90, "Server 1"],
    "s2":     [560, 150, 740, 190, "Server 2"],
    "s3":     [560, 250, 740, 290, "Server 3"]
  },
  "wires": [
    [[160,170],[230,170]],
    [[390,170],[470,170],[470,70],[560,70]],
    [[470,170],[560,170]],
    [[470,170],[470,270],[560,270]]
  ],
  "moves": [
    { "start": 5,   "end": 19,  "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "primary", "label": "req" },
    { "start": 22,  "end": 36,  "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "primary", "label": "req" },
    { "start": 44,  "end": 58,  "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "primary", "label": "req" },
    { "start": 60,  "end": 74,  "path": [[160,170],[390,170],[470,170],[560,170]], "color": "primary", "label": "req" },
    { "start": 76,  "end": 90,  "path": [[160,170],[390,170],[470,170],[470,270],[560,270]], "color": "primary", "label": "req" },
    { "start": 92,  "end": 106, "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "primary", "label": "req" },
    { "start": 108, "end": 122, "path": [[160,170],[390,170],[470,170],[560,170]], "color": "primary", "label": "req" },
    { "start": 140, "end": 154, "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "secondary", "label": "req" },
    { "start": 156, "end": 170, "path": [[160,170],[390,170],[470,170],[470,270],[560,270]], "color": "secondary", "label": "req" },
    { "start": 172, "end": 186, "path": [[160,170],[390,170],[470,170],[470,70],[560,70]], "color": "secondary", "label": "req" },
    { "start": 188, "end": 202, "path": [[160,170],[390,170],[470,170],[470,270],[560,270]], "color": "secondary", "label": "req" }
  ],
  "captions": [
    { "start": 0,   "end": 40,  "text": "one server behind the load balancer", "color": "primary" },
    { "start": 40,  "end": 126, "text": "Servers 2 and 3 join: requests go round-robin", "color": "primary" },
    { "start": 126, "end": 190, "text": "Server 2 goes down: health checks fail, so the LB skips it", "color": "secondary" },
    { "start": 190, "end": 999, "text": "lose one, traffic keeps flowing to Servers 1 and 3", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

Failover isn't instant. Between the crash and the failed health checks (a few seconds with typical settings), requests already sent to the dead server fail. Clients and the load balancer need retries for idempotent requests, or users see a burst of errors. This is also how [Kubernetes](../../kubernetes/deployment-pipeline.md) treats replicas: readiness probes play the health-check role, and a Deployment replaces pods that die.

Scaling out is also how you buy safety, not only capacity. Two small servers survive a failure that takes one big server down. The catch is headroom: if three servers each run at 90%, losing one pushes the other two to 135%. They're over capacity, so one failed server takes the whole fleet down with it. Size the fleet so the remaining servers can carry peak traffic with one gone (N+1). Leave room beyond that too: as [Day 1 on latency vs throughput](../latency-vs-throughput/index.md) showed, latency climbs steeply well before a server hits 100%. The calculator below does the sizing math.

## The stateless rule

Scale-out only works when any server can answer any request. If a user's session lives in one server's memory, the next request can land on a different server and find nothing.

{{< mermaid >}}
sequenceDiagram
  participant C as Client
  participant LB as Load balancer
  participant S1 as Server 1
  participant S2 as Server 2
  participant R as Redis
  C->>LB: POST /login
  LB->>S1: route
  S1->>S1: session kept in memory
  C->>LB: GET /cart
  LB->>S2: route
  Note over S2: no session here, user looks logged out
  Note over S1,R: fix: sessions live in Redis
  S1->>R: save session
  S2->>R: load session
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Stateless servers",
  "subtitle": "State moves out of server memory",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 200,
  "boxes": {
    "client": [20, 150, 160, 190, "Client"],
    "lb":     [220, 150, 380, 190, "Load balancer"],
    "s1":     [470, 60, 630, 100, "Server 1"],
    "s2":     [470, 240, 630, 280, "Server 2"],
    "redis":  [680, 150, 790, 190, "Redis"]
  },
  "wires": [
    [[160,170],[220,170]],
    [[380,170],[425,170],[425,80],[470,80]],
    [[425,170],[425,260],[470,260]],
    [[630,80],[735,80],[735,150]],
    [[630,260],[735,260],[735,190]]
  ],
  "moves": [
    { "start": 5,   "end": 30,  "path": [[160,170],[380,170],[425,170],[425,80],[470,80]], "color": "primary", "label": "login" },
    { "start": 40,  "end": 65,  "path": [[160,170],[380,170],[425,170],[425,260],[470,260]], "color": "secondary", "label": "GET /cart" },
    { "start": 85,  "end": 108, "path": [[160,170],[380,170],[425,170],[425,80],[470,80]], "color": "primary", "label": "login" },
    { "start": 110, "end": 126, "path": [[630,80],[735,80],[735,150]], "color": "primary", "label": "save session" },
    { "start": 136, "end": 159, "path": [[160,170],[380,170],[425,170],[425,260],[470,260]], "color": "primary", "label": "GET /cart" },
    { "start": 161, "end": 177, "path": [[630,260],[735,260],[735,190]], "color": "primary", "label": "load session" }
  ],
  "captions": [
    { "start": 0,   "end": 36,  "text": "request 1 lands on Server 1, which keeps the session in memory", "color": "primary" },
    { "start": 36,  "end": 80,  "text": "request 2 lands on Server 2: no session, user looks logged out", "color": "secondary" },
    { "start": 80,  "end": 132, "text": "fix: Server 1 writes the session to Redis", "color": "primary" },
    { "start": 132, "end": 999, "text": "Server 2 reads it back, so any server can answer any request", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

There are three common fixes, each with a cost:

- **Shared session store** (Redis, Memcached, or the database). Every request does one extra network hop to load the session. It works with any client.
- **Signed token** (a JWT or a signed cookie). The client carries the state and any server can verify it with the signing key, so no lookup is needed. Revoking a token before it expires is hard, so keep expiry short.
- **Sticky sessions** at the load balancer pin a user to one server. It's a stopgap. Load gets uneven, and when that server dies its users lose their sessions anyway.

Sessions aren't the only state. Uploaded files on local disk, in-process caches and scheduled jobs that assume one instance all break the same way once there are two servers. Move files to object storage, accept that local caches differ per server, and use a lock or a leader for jobs that must run once.

## The database is the wall

Each counter sells from the same stock room. Once the app tier is stateless and scaled out, every server talks to one database, and that's where the next limit shows up. Connections run out first: 20 app servers with a pool of 20 each want 400 connections, and Postgres ships with `max_connections = 100`. A connection pooler like PgBouncer helps. After that comes CPU and disk on the primary.

**Read replicas** come first. Most apps read far more than they write, so sending reads to replicas takes load off the primary. The cost is replication lag: a user who just saved a change and reads from a replica might not see it yet. **Sharding** splits writes across databases by a key, and it comes much later, because cross-shard queries and transactions get hard. Both get their own day in this series. The same idea shows up in [Kafka partitions](../../kafka/apache-kafka-concepts/index.md), which are how Kafka spreads writes across brokers.

Scaling the app tier also changes your deploys. With [independent services](../../architecture/microservices-fundamentals.md), each one can scale on its own, but the shared database still caps them all.

## Sizing it

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Traffic and servers",
      "inputs": [
        { "id": "peakRps", "label": "Peak traffic", "default": 2500, "step": 100, "unit": "req/s" },
        { "id": "rpsPerServer", "label": "Capacity of one server", "default": 1000, "step": 100, "unit": "req/s" },
        { "id": "servers", "label": "Servers behind the load balancer", "default": 4, "step": 1 }
      ],
      "outputs": [
        { "id": "needed", "label": "Servers needed to carry peak", "formula": "Math.ceil(peakRps / rpsPerServer)", "format": "number" },
        { "id": "utilAllUp", "label": "Load per server, all up (%)", "formula": "peakRps / (Math.floor(servers) * rpsPerServer) * 100", "format": "number" },
        { "id": "utilOneDown", "label": "Load per server, one down (%)", "formula": "Math.floor(servers) > 1 ? peakRps / ((Math.floor(servers) - 1) * rpsPerServer) * 100 : NaN", "format": "number" }
      ]
    },
    {
      "title": "Availability",
      "inputs": [
        { "id": "serverAvailPct", "label": "Uptime of one server", "default": 99.5, "step": 0.1, "unit": "%" }
      ],
      "outputs": [
        { "id": "fleetAvailPct", "label": "Fleet uptime: enough servers up (%)", "formula": "(() => { const n = Math.floor(servers), p = Math.min(Math.max(serverAvailPct / 100, 0), 1), k = needed; if (!(n >= k)) return 0; let c = 1, s = 0; for (let i = 0; i <= n; i++) { if (i > 0) c = c * (n - i + 1) / i; if (i >= k) s += c * Math.pow(p, i) * Math.pow(1 - p, n - i); } return s * 100; })()", "format": "number" },
        { "id": "fleetDownHours", "label": "Fleet: hours/year short of capacity", "formula": "(100 - fleetAvailPct) / 100 * 8760", "format": "number" },
        { "id": "bigDownHours", "label": "One big server: hours/year down", "formula": "(100 - Math.min(Math.max(serverAvailPct, 0), 100)) / 100 * 8760", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

The model assumes servers fail independently, load splits evenly, capacity adds linearly, and the load balancer and database never fail. Real fleets share racks and deploys, so treat the fleet number as a best case. A dash means the value is undefined, such as the one-down load with a single server. With the defaults, 2,500 req/s needs 3 servers of 1,000 req/s. Run 4 and each sits at 62.5%, rising to 83.3% with one down. The fleet has enough servers up 99.985% of the time (shown rounded to 99.99), which is about 1.3 hours a year short of capacity. One big server with the same 99.5% uptime is down about 43.8 hours a year. Set servers to 3 and the one-down load goes to 125%: three servers carry the peak, but they can't absorb a failure.

## In practice

Start vertical. It's the cheapest fix and buys you time while you make the app stateless. Then scale out, for capacity and for safety, and expect the database to be the next wall. The [back-of-the-envelope estimation](../back-of-the-envelope-estimation.md) note covers how to get the peak request rate you'd put in the calculator. Scale up to buy time. Scale out to survive.
