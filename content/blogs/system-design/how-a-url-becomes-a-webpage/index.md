---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-10-24T00:00:00+08:00
title: How a URL Becomes a Webpage
tags: [system-design, performance]
categories: [System Design]
mermaid: true
---

Between pressing Enter and getting the first byte of a response (time to first byte, TTFB), the browser runs four steps in order. DNS resolves the hostname to an IP address, usually from a cache. TCP opens a connection with a three-way handshake, which costs one round trip. TLS agrees on encryption keys and checks the server's certificate, which costs one more round trip on TLS 1.3 and two on TLS 1.2. Only then does HTTP send `GET /` and wait. On a first visit, most of that wait goes to setup round trips. Server time is a small part of it, and each round trip costs more the farther the user is from the server. A 50 ms backend behind a 200 ms mobile link and TLS 1.2 still gives about one second to first byte. The fixes all come down to doing fewer round trips or shorter ones: reuse connections, terminate them near the user, use newer protocols that merge handshakes, and tune DNS caching on purpose. Rendering comes after the first byte and is out of scope here.

## The bank call analogy

You are calling a bank for the first time. You look up the phone number (DNS), wait for someone to pick up (TCP), confirm it's really the bank and agree to talk in code (TLS), and then ask your question (HTTP). If you call again on the same open line, you go straight to the question. That's keep-alive: reusing an open connection so later requests skip DNS, TCP and TLS.

Each of the first three steps is a conversation with someone far away, and you can't start the next one until the last reply arrives. That's why the distance counts so much.

## The four steps, in order

**DNS.** The browser checks its own cache, then the operating system's, then asks a recursive resolver (your ISP's, or a public one). If the resolver has the answer cached, the cost is one short round trip to the resolver. On a cold lookup the resolver walks the hierarchy: a root server tells it who runs `.com`, the TLD server tells it who runs the domain, and the domain's authoritative name server returns the IP. In practice resolvers keep the root and TLD answers cached for days, so a "cold" lookup is usually one or two extra hops, not three.

**TCP.** The client sends SYN, the server replies SYN-ACK, and the client sends ACK. The client can send data right behind its ACK, so the handshake costs one full round trip before anything useful moves.

**TLS.** The client sends a ClientHello listing what it supports. The server answers with its choice, its certificate and its key share. On TLS 1.3 (RFC 8446) that one exchange is enough, and the client sends its encrypted request straight after. TLS 1.2 needs a second exchange to finish the key agreement, so it costs two round trips.

**HTTP.** The request goes out, the server does its work, and the first byte of the response comes back. That's one more round trip plus server time.

{{< mermaid >}}
sequenceDiagram
  participant B as Browser
  participant R as DNS resolver
  participant N as Root / TLD / Authoritative
  participant S as Server
  B->>R: where is mybank.com?
  R->>N: cold lookup only
  N-->>R: 203.0.113.10
  R-->>B: 203.0.113.10
  B->>S: SYN
  S-->>B: SYN-ACK
  B->>S: ACK + ClientHello
  S-->>B: ServerHello + certificate
  B->>S: Finished + GET /
  Note over S: 50 ms of server work
  S-->>B: first byte
  B->>S: GET /api (same connection)
  S-->>B: first byte
{{< /mermaid >}}

The animation runs the same exchange for a user 100 ms (round trip) from the server, on TLS 1.3, with a cold DNS lookup that takes 80 ms. Watch the counter. The server works for 50 ms of the 430.

{{< moving-diagram >}}
{
  "title": "From Enter to first byte",
  "subtitle": "100 ms round trip, TLS 1.3, cold DNS, 50 ms of server work",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 300,
  "boxes": {
    "browser":  [40, 160, 200, 240, "Browser", "you press Enter"],
    "resolver": [300, 30, 440, 80, "DNS resolver", "recursive"],
    "ns":       [560, 30, 760, 80, "Root / TLD / Auth", "cold lookup only"],
    "server":   [600, 160, 760, 240, "Server", "100 ms round trip"]
  },
  "wires": [
    [[120,160],[120,55],[300,55]],
    [[440,55],[560,55]],
    [[200,180],[600,180]],
    [[600,220],[200,220]]
  ],
  "moves": [
    { "start": 0,   "end": 12,  "path": [[120,160],[120,55],[300,55]], "color": "primary", "label": "DNS query" },
    { "start": 14,  "end": 26,  "path": [[440,55],[560,55]], "color": "primary", "label": "walk" },
    { "start": 28,  "end": 40,  "path": [[560,55],[440,55]], "color": "primary", "label": "IP" },
    { "start": 42,  "end": 54,  "path": [[300,55],[120,55],[120,160]], "color": "primary", "label": "203.0.113.10" },
    { "start": 60,  "end": 76,  "path": [[200,180],[600,180]], "color": "primary", "label": "SYN" },
    { "start": 78,  "end": 94,  "path": [[600,220],[200,220]], "color": "primary", "label": "SYN-ACK" },
    { "start": 98,  "end": 114, "path": [[200,180],[600,180]], "color": "primary", "label": "ACK + ClientHello" },
    { "start": 116, "end": 132, "path": [[600,220],[200,220]], "color": "primary", "label": "ServerHello + cert" },
    { "start": 136, "end": 152, "path": [[200,180],[600,180]], "color": "secondary", "label": "Finished + GET /" },
    { "start": 166, "end": 182, "path": [[600,220],[200,220]], "color": "secondary", "label": "first byte" },
    { "start": 204, "end": 220, "path": [[200,180],[600,180]], "color": "secondary", "label": "GET /api" },
    { "start": 234, "end": 250, "path": [[600,220],[200,220]], "color": "secondary", "label": "first byte" }
  ],
  "tags": [
    { "start": 0,   "end": 54,  "x": 400, "y": 300, "text": "elapsed: 0 ms", "color": "primary" },
    { "start": 54,  "end": 76,  "x": 400, "y": 300, "text": "elapsed: 80 ms   (DNS done)", "color": "primary" },
    { "start": 76,  "end": 94,  "x": 400, "y": 300, "text": "elapsed: 130 ms", "color": "primary" },
    { "start": 94,  "end": 114, "x": 400, "y": 300, "text": "elapsed: 180 ms   (TCP done)", "color": "primary" },
    { "start": 114, "end": 132, "x": 400, "y": 300, "text": "elapsed: 230 ms", "color": "primary" },
    { "start": 132, "end": 152, "x": 400, "y": 300, "text": "elapsed: 280 ms   (TLS done)", "color": "primary" },
    { "start": 152, "end": 166, "x": 400, "y": 300, "text": "elapsed: 330 ms", "color": "secondary" },
    { "start": 166, "end": 182, "x": 400, "y": 300, "text": "elapsed: 380 ms", "color": "secondary" },
    { "start": 182, "end": 200, "x": 400, "y": 300, "text": "elapsed: 430 ms   (first byte)", "color": "secondary" },
    { "start": 152, "end": 166, "x": 680, "y": 262, "text": "working 50 ms", "color": "secondary" },
    { "start": 200, "end": 220, "x": 400, "y": 300, "text": "request 2: 0 ms", "color": "secondary" },
    { "start": 220, "end": 234, "x": 400, "y": 300, "text": "request 2: 50 ms", "color": "secondary" },
    { "start": 220, "end": 234, "x": 680, "y": 262, "text": "working 50 ms", "color": "secondary" },
    { "start": 234, "end": 250, "x": 400, "y": 300, "text": "request 2: 100 ms", "color": "secondary" },
    { "start": 250, "end": 300, "x": 400, "y": 300, "text": "request 2: 150 ms   (first byte)", "color": "secondary" }
  ],
  "captions": [
    { "start": 0,   "end": 58,  "text": "DNS: find the IP (cold lookup walks the hierarchy)", "color": "primary" },
    { "start": 58,  "end": 96,  "text": "TCP: SYN, SYN-ACK. One round trip", "color": "primary" },
    { "start": 96,  "end": 134, "text": "TLS 1.3: hello, certificate, keys. One round trip", "color": "primary" },
    { "start": 134, "end": 196, "text": "HTTP: GET /, 50 ms of work, first byte back", "color": "secondary" },
    { "start": 196, "end": 256, "text": "keep-alive: request 2 skips DNS, TCP and TLS", "color": "secondary" },
    { "start": 256, "end": 999, "text": "first byte = DNS + TCP + TLS + HTTP = 80+100+100+150", "color": "secondary" }
  ]
}
{{< /moving-diagram >}}

## Where the second goes

Take the post's opening case: a 50 ms backend, a user on a mobile network with a 200 ms round trip, a site still on TLS 1.2, and a DNS lookup the resolver hasn't cached (call it 150 ms). DNS is 150. TCP is 200. TLS 1.2 is 400. HTTP is 200 plus 50. That adds up to 1,000 ms, and the server's share is 5%.

Now change one thing at a time. Moving to TLS 1.3 saves 200 ms. A warm DNS cache saves 150. Keep-alive makes the second request cost 250 ms instead of 850. Speeding up the server by 25 ms gets you 2.5%.

So a faster backend makes only a small dent in first-visit TTFB once the user is far away, which is why profiling only the server is misleading. The [Latency vs Throughput](../latency-vs-throughput/) note makes the same point from the physics side: light in fiber covers about 200 km per millisecond, and no code change shortens that.

Play with the numbers below. Set the round trip to 20 ms (a user near a data center) and the server becomes the largest piece again.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "Connection",
      "inputs": [
        { "id": "rtt", "label": "Round trip to the server", "default": 200, "step": 10, "unit": "ms" },
        { "id": "dns", "label": "DNS lookup (0 if cached)", "default": 150, "step": 10, "unit": "ms" },
        { "id": "tlsRtts", "label": "TLS round trips (2 = TLS 1.2, 1 = TLS 1.3, 0 = plain HTTP)", "default": 2, "step": 1 },
        { "id": "serverMs", "label": "Server time per request", "default": 50, "step": 5, "unit": "ms" }
      ],
      "outputs": [
        { "id": "setupMs", "label": "Setup before the request (ms)", "formula": "dns + rtt + tlsRtts * rtt", "format": "number" },
        { "id": "coldTtfb", "label": "First visit, time to first byte (ms)", "formula": "setupMs + rtt + serverMs", "format": "number" },
        { "id": "serverShare", "label": "Server share of first-visit TTFB (%)", "formula": "coldTtfb > 0 ? serverMs / coldTtfb * 100 : 0", "format": "number" },
        { "id": "quicTtfb", "label": "Same visit over HTTP/3 (QUIC) (ms)", "formula": "dns + 2 * rtt + serverMs", "format": "number" },
        { "id": "warmTtfb", "label": "Next request on the open connection (ms)", "formula": "rtt + serverMs", "format": "number" }
      ]
    },
    {
      "title": "Several requests, one after another",
      "inputs": [
        { "id": "requests", "label": "Requests to the same host", "default": 5, "step": 1 }
      ],
      "outputs": [
        { "id": "withKeepAlive", "label": "Total with keep-alive (ms)", "formula": "coldTtfb + (Math.max(1, requests) - 1) * warmTtfb", "format": "number" },
        { "id": "withoutKeepAlive", "label": "Total with a new connection each time (ms)", "formula": "coldTtfb + (Math.max(1, requests) - 1) * (rtt + tlsRtts * rtt + rtt + serverMs)", "format": "number" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

The model assumes requests run one after another, there's no packet loss, server time is the same every time, DNS is paid only once, the TCP and TLS handshakes don't overlap (no TCP Fast Open or 0-RTT resumption), and QUIC always takes one combined handshake round trip whatever the TLS input says. Hand check with the defaults: setup is 150 + 200 + 400 = 750 ms, first visit is 750 + 200 + 50 = 1,000 ms, server share is 5%, QUIC is 150 + 400 + 50 = 600 ms, and a warm request is 250 ms. Five requests come to 1,000 + 4 × 250 = 2,000 ms with keep-alive and 1,000 + 4 × 850 = 4,400 ms without it.

## The levers, and when each one backfires

**Reuse connections.** In browsers, HTTP/1.1 connections stay open by default and HTTP/2 multiplexes many requests over one. The more common leak is server-to-server: a service that builds a new HTTP client per call (in Java, a new `HttpClient` each time) pays TCP and TLS on every call and burns CPU on handshakes. Keep one client and let its pool do the work. There are two ways this goes wrong. Load balancers close idle connections (AWS ALB's default idle timeout is 60 seconds), and if your pool keeps connections idle longer than that, the next request goes out on a socket the other side already closed and fails with a connection reset. Set the client's idle timeout below the server's. Long-lived connections also stay pinned to one backend. After you [scale out horizontally](../vertical-vs-horizontal-scaling/), the new instances can sit idle while old connections keep feeding the old ones, so cap connection lifetime too.

**Terminate near the user.** A CDN edge 20 ms away runs TCP and TLS over 20 ms round trips. It keeps warm connections to your origin, so a cache miss pays one origin round trip and no origin handshakes. A cache hit never reaches the origin.

{{< mermaid >}}
sequenceDiagram
  participant B as Browser
  participant E as CDN edge (20 ms)
  participant O as Origin (90 ms from edge)
  B->>E: SYN
  E-->>B: SYN-ACK
  B->>E: ACK + ClientHello
  E-->>B: ServerHello + certificate
  B->>E: Finished + GET /
  E->>O: GET / (connection already open)
  Note over O: 50 ms of server work
  O-->>E: response
  E-->>B: first byte
  B->>E: GET /logo.png
  E-->>B: first byte (cache hit)
{{< /mermaid >}}

{{< moving-diagram >}}
{
  "title": "Handshakes at the edge",
  "subtitle": "Edge 20 ms from the user, origin 90 ms from the edge, TLS 1.3, DNS cached",
  "viewBox": "0 0 800 400",
  "fps": 25,
  "totalFrames": 240,
  "boxes": {
    "browser": [30, 160, 170, 240, "Browser"],
    "edge":    [330, 160, 470, 240, "CDN edge", "20 ms round trip"],
    "origin":  [630, 160, 770, 240, "Origin", "connection kept warm"]
  },
  "wires": [
    [[170,180],[330,180]],
    [[330,220],[170,220]],
    [[470,180],[630,180]],
    [[630,220],[470,220]]
  ],
  "moves": [
    { "start": 0,   "end": 8,   "path": [[170,180],[330,180]], "color": "primary", "label": "SYN" },
    { "start": 10,  "end": 18,  "path": [[330,220],[170,220]], "color": "primary", "label": "SYN-ACK" },
    { "start": 20,  "end": 28,  "path": [[170,180],[330,180]], "color": "primary", "label": "ClientHello" },
    { "start": 30,  "end": 38,  "path": [[330,220],[170,220]], "color": "primary", "label": "ServerHello" },
    { "start": 40,  "end": 48,  "path": [[170,180],[330,180]], "color": "secondary", "label": "GET /" },
    { "start": 50,  "end": 75,  "path": [[470,180],[630,180]], "color": "secondary", "label": "GET / (reused)" },
    { "start": 89,  "end": 114, "path": [[630,220],[470,220]], "color": "secondary", "label": "response" },
    { "start": 116, "end": 124, "path": [[330,220],[170,220]], "color": "secondary", "label": "first byte" },
    { "start": 150, "end": 158, "path": [[170,180],[330,180]], "color": "primary", "label": "GET /logo.png" },
    { "start": 162, "end": 170, "path": [[330,220],[170,220]], "color": "primary", "label": "cache hit" }
  ],
  "tags": [
    { "start": 0,   "end": 38,  "x": 400, "y": 300, "text": "handshakes: 2 round trips x 20 ms", "color": "primary" },
    { "start": 38,  "end": 48,  "x": 400, "y": 300, "text": "elapsed: 40 ms", "color": "primary" },
    { "start": 48,  "end": 75,  "x": 400, "y": 300, "text": "elapsed: 50 ms", "color": "secondary" },
    { "start": 75,  "end": 89,  "x": 400, "y": 300, "text": "elapsed: 95 ms", "color": "secondary" },
    { "start": 75,  "end": 89,  "x": 700, "y": 262, "text": "working 50 ms", "color": "secondary" },
    { "start": 89,  "end": 114, "x": 400, "y": 300, "text": "elapsed: 145 ms", "color": "secondary" },
    { "start": 114, "end": 124, "x": 400, "y": 300, "text": "elapsed: 190 ms", "color": "secondary" },
    { "start": 124, "end": 146, "x": 400, "y": 300, "text": "elapsed: 200 ms   (first byte)", "color": "secondary" },
    { "start": 146, "end": 240, "x": 400, "y": 300, "text": "cache hit: 20 ms", "color": "primary" }
  ],
  "captions": [
    { "start": 0,   "end": 40,  "text": "TCP and TLS 1.3 run against an edge 20 ms away", "color": "primary" },
    { "start": 40,  "end": 126, "text": "cache miss: one origin round trip, no origin handshakes", "color": "secondary" },
    { "start": 126, "end": 148, "text": "200 ms to first byte, vs 350 ms direct at 100 ms round trip", "color": "secondary" },
    { "start": 148, "end": 999, "text": "cache hit: the origin never sees the request", "color": "primary" }
  ]
}
{{< /moving-diagram >}}

A CDN is the wrong choice when every response is personalised and uncacheable *and* your users already sit near the origin: you add a hop and a vendor and save very little. It also hides problems. If the edge keeps serving stale content after a bad deploy, your purge process is now part of your incident response.

**Merge handshakes.** TLS 1.3 halves the TLS cost. HTTP/3 runs over QUIC, which does the transport and TLS handshakes in one round trip. Two caveats. The browser usually learns a site supports HTTP/3 from an `Alt-Svc` header on an earlier TCP response, so the very first visit often still goes over TCP. Some corporate and public networks block UDP, and clients then fall back to TCP, so keep the TCP path fast. TLS 1.3 also offers 0-RTT resumption, where a returning client sends its request with the first flight. An attacker can replay that early data, so only allow it for idempotent requests. Nobody wants a replayed `POST /payments`.

**Set DNS TTLs on purpose.** A 30-second TTL means resolvers keep asking, and more of your users hit cold lookups. A one-day TTL means that when you fail over to a new IP, part of your traffic keeps going to the dead one for hours. Clients cache too: the JVM caches successful lookups for 30 seconds by default (`networkaddress.cache.ttl`), and some resolvers stretch TTLs past what you set. A common middle ground is a few minutes for records you might fail over, and lowering the TTL a day ahead of a planned migration.

## What to measure

Split TTFB into its parts before you change anything. From a terminal:

```bash
curl -o /dev/null -s -w 'dns  %{time_namelookup}\ntcp  %{time_connect}\ntls  %{time_appconnect}\nttfb %{time_starttransfer}\n' https://example.com/
```

The values are cumulative seconds from the start, so the TLS cost is `time_appconnect - time_connect`. In the browser, `PerformanceNavigationTiming` gives the same split (`domainLookupStart`, `connectStart`, `secureConnectionStart`, `requestStart`, `responseStart`) for real users. Have the server report its own time with a `Server-Timing: app;dur=48` header. TTFB minus server time is what the network and the handshakes cost you.

Group these by region and connection type, and look at p75 and p99 rather than the mean. Your office laptop on fiber next to the data center tells you nothing about a user on a train. Mobile users feel this most, because every round trip on a mobile network is slow, and setup on a first visit is several round trips back to back.
