---
draft: false
weight: 10
showAuthor: true
showWordCount: true
showReadingTime: true
title: Back-of-the-Envelope Estimation for System Design
---
Before you draw a single box in a system design, you need a rough sense of scale — how many users, how many requests per second, how much data you're storing, how much bandwidth you need. Back-of-the-envelope estimation is the practice of turning a few known numbers (users, activity, message size) into these scale numbers using simple arithmetic. It doesn't need to be precise; it needs to tell you whether you're building something that fits on one server or something that needs to be sharded across a thousand.

The technique is always the same shape: start from **user metrics** you're given or can reasonably assume, derive **request/message rates** from them, then derive **storage** and **bandwidth** from those rates. Each stage feeds the next, so a mistake or a changed assumption early on ripples through everything downstream — which is exactly why it helps to make the calculation live instead of doing it once on paper.

Below is a worked example for a WhatsApp-style messaging service. Change any of the input numbers and everything downstream recalculates automatically.

{{< back-of-envelope >}}
{
  "sections": [
    {
      "title": "User metrics",
      "inputs": [
        { "id": "registeredUsers", "label": "Registered users", "default": 1000000000, "step": 1000000 },
        { "id": "dauPercent", "label": "Daily active users", "default": 50, "step": 1, "unit": "%" },
        { "id": "msgsPerUserPerDay", "label": "Avg messages per user / day", "default": 20, "step": 1 },
        { "id": "peakMultiplier", "label": "Peak-hour multiplier", "default": 4, "step": 0.5 }
      ]
    },
    {
      "title": "Message estimations",
      "outputs": [
        { "id": "dau", "label": "Daily active users", "formula": "registeredUsers * (dauPercent / 100)", "format": "compact" },
        { "id": "dailyMessages", "label": "Daily messages", "formula": "dau * msgsPerUserPerDay", "format": "compact" },
        { "id": "avgMsgsPerSec", "label": "Avg messages / sec", "formula": "dailyMessages / 86400", "format": "number" },
        { "id": "peakMsgsPerSec", "label": "Peak messages / sec", "formula": "avgMsgsPerSec * peakMultiplier", "format": "number" }
      ]
    },
    {
      "title": "Storage calculation",
      "inputs": [
        { "id": "bytesPerMessage", "label": "Bytes per message (with metadata)", "default": 1024, "step": 64 }
      ],
      "outputs": [
        { "id": "dailyStorage", "label": "Daily storage", "formula": "dailyMessages * bytesPerMessage", "format": "bytes" },
        { "id": "annualStorage", "label": "Annual storage", "formula": "dailyStorage * 365", "format": "bytes" }
      ]
    },
    {
      "title": "Bandwidth",
      "inputs": [
        { "id": "concurrentConnections", "label": "Concurrent connections at peak", "default": 50000000, "step": 1000000 },
        { "id": "bytesPerSecPerConnection", "label": "Bytes/sec per active connection", "default": 10240, "step": 1024 }
      ],
      "outputs": [
        { "id": "peakBandwidth", "label": "Peak bandwidth", "formula": "concurrentConnections * bytesPerSecPerConnection", "format": "bytes" }
      ]
    }
  ]
}
{{< /back-of-envelope >}}

A few things worth noticing about the chain above:

- **Message estimations** derives everything from `registeredUsers` and `dauPercent` — bump the DAU percentage and both the daily message count and the peak throughput move with it.
- **Storage calculation** reaches back into `dailyMessages` from the section above it, rather than recomputing it — this is what makes the sections composable instead of a wall of duplicated formulas.
- **Peak-hour multiplier** is a judgment call (3-5x average is a common rule of thumb for chat/social traffic), not a measured number — estimation is as much about naming your assumptions explicitly as it is about the arithmetic.

None of these numbers need to be exact. What matters is landing in the right order of magnitude — whether storage is measured in gigabytes, terabytes, or petabytes changes the entire architecture, and that's the question this kind of estimation is meant to answer.
