---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-09-14
title: Spring Boot Core Concepts
tags: [spring-boot, spring, java, dependency-injection]
categories: [Java]
mermaid: true
---

Spring Boot removes manual Spring configuration through three mechanisms: auto-configuration (conditional bean registration based on classpath + existing beans), an embedded server plus starter dependencies (curated dependency bundles), and production-ready defaults via Actuator. The bean lifecycle follows a fixed 9-step sequence, dependency injection should default to the constructor form, and a "starter" is a dependency descriptor, not runtime code.

For what `@SpringBootApplication` itself actually does under the hood, see [What Really Happens When You Add @SpringBootApplication?]({{< ref "../spring/spring-boot-application-annotation.md" >}}) — in short, it's a meta-annotation combining `@SpringBootConfiguration`, `@EnableAutoConfiguration` (the mechanism below), and `@ComponentScan`. The default embedded server for a typical web app is **Tomcat, via Spring MVC** (not Jersey).

## Dependency injection and the bean lifecycle

Two separate steps happen: (a) **bean registration** — stereotype annotations (`@Component`, `@Service`, `@Repository`, `@Controller`) mark a class to be picked up by component scanning; (b) **dependency injection** — the actual wiring of one bean into another, via constructor (preferred) or `@Autowired` field/setter.

Full bean lifecycle, in order:

{{< mermaid >}}
flowchart TD
  A["1. Bean definitions loaded\n(component scan / @Configuration)"] --> B["2. Instantiation\n(constructor called)"]
  B --> C["3. Dependency injection\n(fields/setters populated)"]
  C --> D["4. Aware callbacks\n(BeanNameAware, ApplicationContextAware...)"]
  D --> E["5. BeanPostProcessor\npostProcessBeforeInitialization"]
  E --> F["6. Init callbacks\n@PostConstruct -> afterPropertiesSet() -> init-method"]
  F --> G["7. BeanPostProcessor\npostProcessAfterInitialization\n(AOP proxy created HERE)"]
  G --> H["8. Bean ready\n(cached in container)"]
  H --> I["9. Destruction (singleton only)\n@PreDestroy -> destroy() -> destroy-method"]
{{< /mermaid >}}

Say it out loud as: **load → build → wire → make aware → pre-init hook → initialize → post-init hook (proxy wraps here) → ready → destroy.**

**Scopes:** `singleton` (default — one instance per container), `prototype` (a new instance every injection/lookup), and the web-aware scopes — `request`, `session`, `application`, `websocket`.
- Use `prototype` for a bean holding mutable, non-thread-safe state per use (e.g. a stateful builder/accumulator) — you don't want threads sharing one instance.
- Use `request` scope for web-tier state that should live only for one HTTP request (e.g. a resolved tenant/user context cached so you don't re-resolve it in every layer).

**Gotcha worth knowing:** a singleton bean injecting a prototype bean gets only *one* prototype instance forever (wired once at startup) unless you use a scoped proxy (`proxyMode = ScopedProxyMode.TARGET_CLASS`) or `ObjectProvider`/`ObjectFactory` to fetch a fresh instance on demand. Also, Spring does **not** call destroy callbacks on prototype beans — cleanup of those is the caller's responsibility.

## How auto-configuration decides what to configure

`@EnableAutoConfiguration` reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (a plain text list of hundreds of candidate `@Configuration` classes bundled in `spring-boot-autoconfigure.jar` — e.g. `DataSourceAutoConfiguration`, `TomcatServletWebServerFactoryAutoConfiguration`). Every one of these is evaluated on every startup, gated by conditional annotations:
- `@ConditionalOnClass` — applies only if a given class is on the classpath (why adding a JDBC driver jar "turns on" `DataSourceAutoConfiguration` — it's classpath detection, not the starter doing anything special).
- `@ConditionalOnMissingBean` — applies only if you haven't already defined your own bean of that type (your `@Bean` always wins over the auto-configured default).
- `@ConditionalOnProperty`, `@ConditionalOnWebApplication` — gate on config properties / app type.

Ordering between auto-config classes is controlled via `@AutoConfigureAfter`/`@AutoConfigureBefore`.

{{< mermaid >}}
flowchart TD
  A["App starts — @EnableAutoConfiguration fires"] --> B["Read AutoConfiguration.imports\n(hundreds of candidate @Configuration classes)"]
  B --> C{"For each candidate:\nconditions satisfied?"}
  C -->|"@ConditionalOnClass matches\nAND no conflicting bean"| D["Bean registered\n(positive match)"]
  C -->|"condition fails"| E["Skipped\n(negative match)"]
  D --> F["Visible via --debug ->\nConditions Evaluation Report"]
  E --> F
{{< /mermaid >}}

**Debugging "why isn't X getting auto-configured":** run with `--debug` (or `debug=true` in properties) — prints the **Conditions Evaluation Report** on startup: every auto-configuration class split into "Positive matches" and "Negative matches," each with the exact reason (e.g. "did not match: required class 'javax.sql.DataSource' was not found"). Also available at runtime via `/actuator/conditions`. Force-disable one explicitly with `@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)`.
One-liner: "classpath + conditional annotations + a text file listing candidate configs."

## Diagnosing a REST endpoint that's fast in isolation but slow under load

The core insight: a single request never contends for a shared, finite resource — many concurrent requests do. Ranked causes, roughly most-to-least common:
1. **Thread pool exhaustion** — Tomcat's embedded worker pool is fixed (default ~200). If a handler does anything blocking (JDBC call, blocking HTTP call), each concurrent request holds a thread for the duration; once concurrent requests exceed the pool size, new requests queue and latency falls off a cliff. (This is exactly the problem a reactive/WebFlux rewrite solves — see [Spring WebFlux and Reactive Programming]({{< ref "../spring/webflux-reactive-programming.md" >}}).)
2. **Connection pool exhaustion** — HikariCP's default pool is ~10 connections; more concurrent requests than pooled connections means requests queue for one.
3. **GC pressure** — higher allocation rate under load means more frequent/longer GC pauses, adding to every request's latency (a throughput effect, distinct from a true memory leak, which shows as heap climbing without recovering over time).
4. **CPU saturation** — concurrent requests compete for the same cores.
5. **Downstream amplification** — a dependency with spare capacity for one request starts queueing once several requests hit it concurrently.

**Diagnostic order** — the mental checklist to run through, cheapest/most-likely check first:

{{< mermaid >}}
flowchart TD
  A["Endpoint slow only under load"] --> B{"tomcat.threads.busy\nnear config.max?"}
  B -->|yes| B1["Thread pool exhaustion:\nfind the blocking call in the handler"]
  B -->|no| C{"hikaricp.connections.pending > 0?"}
  C -->|yes| C1["Connection pool exhaustion:\nsize the pool / cut hold time"]
  C -->|no| D{"jvm.gc.pause rising, or\nheap climbing without recovery?"}
  D -->|yes| D1["GC pressure or real leak:\ncheck heap trend over time"]
  D -->|no| E{"CPU near saturation?"}
  E -->|yes| E1["CPU-bound:\nscale out or optimize hot path"]
  E -->|no| F["Downstream dependency amplification:\ncheck its latency under concurrency"]
{{< /mermaid >}}

Backing metrics for each check: `tomcat.threads.busy` vs `.config.max` → `hikaricp.connections.pending`/`.active` vs `.max` → `jvm.gc.pause` + `jvm.memory.used` vs `.max` → `http.server.requests` p50/p95/p99 (reveals "fine alone, bad under load" since p50 can look fine while p99 explodes) → `/actuator/threaddump` for a live incident (many threads `BLOCKED`/`WAITING` on the same lock/resource is the smoking gun). In practice these are scraped into Prometheus/Grafana rather than read raw.

## Building a custom Spring Boot starter

A starter is **a dependency descriptor, not runtime code** — a POM/Gradle module bundling a curated, version-compatible set of dependencies (that's literally what `spring-boot-starter-web` is: no code, just pulls in spring-webmvc + Jackson + embedded Tomcat, etc.).

Standard two-module convention:
1. `acme-spring-boot-autoconfigure` — the real code: `@Configuration` classes gated by `@ConditionalOnClass`/`@ConditionalOnMissingBean`, `@ConfigurationProperties` classes so consumers can override defaults via `application.yml`, and the `AutoConfiguration.imports` file registering those configs (same mechanism as above).
2. `acme-spring-boot-starter` — an empty POM depending on the autoconfigure module plus whatever third-party client library it wraps. This is the artifact app teams actually add.

**Why over a shared library module:** a plain shared library still requires every consuming team to hand-write `@Bean` wiring and guess at sensible config — boilerplate that drifts slightly per team. A starter gives every team the same org-approved defaults out of the box — "add one dependency, get a working, pre-configured client." Examples: a company-wide Kafka-client starter with standardized security/serialization config, a shared observability starter with tracing pre-wired, a resilience-wrapped HTTP client starter with retries/circuit-breaker baked in. It's convention-over-configuration applied at the *organization* level, not just the app level.

## Constructor injection vs. field injection

Use constructor injection by default (the Spring team's own recommendation). Reasons, in order of strength:
1. **Testability** — plain `new MyClass(mockDep)` in a unit test, no Spring context, no reflection, no setters needed.
2. **Immutability** — dependencies can be declared `private final`; the object is fully valid the instant it exists, with no half-wired state (field injection populates non-final fields *after* the no-arg constructor runs).
3. **Fail-fast on circular dependencies** — if class A and class B depend on each other via constructors, the app refuses to start with a clear circular-dependency error. Field/setter injection can silently resolve such cycles via early bean references — meaning a real design smell keeps working instead of forcing a fix.
4. **Visible dependency graph** — a constructor with eight parameters is an obvious, unmissable "this class does too much" signal; the same eight dependencies as scattered `@Autowired` fields are easy to not notice accumulating.

One-liner: "constructor injection — immutable, fail-fast, testable without a container, makes an overloaded class visually obvious."
