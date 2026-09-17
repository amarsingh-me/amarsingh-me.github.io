---
draft: false
weight: 10
showAuthor: true
showWordCount: true
showReadingTime: true
title: What Really Happens When You Add @SpringBootApplication?
mermaid: true
---
Every Spring Boot app starts with the same line of ceremony: a `main` method, a call to `SpringApplication.run(...)`, and a single annotation — `@SpringBootApplication` — sitting on top of the class. It looks like magic, but it isn't one thing at all. It's three annotations wearing a trench coat, and understanding what each of them does is the fastest way to stop being surprised by Spring Boot.

## It's a Meta-Annotation

If you open up the Spring Boot source, `@SpringBootApplication` is declared roughly like this:

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(excludeFilters = {
        @Filter(type = FilterType.CUSTOM, classes = TypeExcludeFilter.class),
        @Filter(type = FilterType.CUSTOM, classes = AutoConfigurationExcludeFilter.class) })
public @interface SpringBootApplication {
    // ...
}
```

So putting `@SpringBootApplication` on your main class is exactly equivalent to stacking these three annotations yourself:

{{< mermaid >}}
%%{init: {'flowchart': {'useMaxWidth': true}}}%%
flowchart LR
    SBA(["@SpringBootApplication"])

    SBA --> SBC["@SpringBootConfiguration<br/>Marks this class as a source<br/>of bean definitions (it's a<br/>specialised @Configuration)"]
    SBA --> EAC["@EnableAutoConfiguration<br/>Guesses & configures beans<br/>based on what's on the classpath"]
    SBA --> CS["@ComponentScan<br/>Scans this package (and below)<br/>for @Component-annotated classes"]

    classDef root  fill:#E6F1FB,stroke:#185FA5,color:#0C447C
    classDef cfg   fill:#E1F5EE,stroke:#0F6E56,color:#085041
    classDef auto  fill:#FAEEDA,stroke:#854F0B,color:#633806
    classDef scan  fill:#EEEDFE,stroke:#534AB7,color:#3C3489

    class SBA root
    class SBC cfg
    class EAC auto
    class CS scan
{{< /mermaid >}}

Two of these are simple. The third is where all the interesting behavior lives.

## `@ComponentScan` — Finding Your Beans

`@ComponentScan` tells Spring where to look for classes annotated with `@Component`, `@Service`, `@Repository`, and `@Controller`. By default, it scans the package that the annotated class lives in, plus every sub-package.

This is exactly why the convention is to put your `@SpringBootApplication` class at the *root* package of your project (e.g. `com.example.app`, with everything else nested underneath). If you moved it into a leaf package, sibling packages would silently fall outside the scan and their beans would never be registered.

## `@EnableAutoConfiguration` — The Part That Feels Like Magic

This is the annotation that lets you add `spring-boot-starter-web` to your `pom.xml`, write zero configuration, and still get an embedded Tomcat server with sensible defaults. Here's the mechanism behind that:

1. At startup, Spring Boot's auto-configuration import selector reads a list of candidate configuration classes from `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (bundled inside `spring-boot-autoconfigure.jar`; older versions used `META-INF/spring.factories` for the same purpose).
2. Every one of those candidates is itself an `@AutoConfiguration` class — but almost none of them are *unconditionally* applied.
3. Each is guarded by one or more `@Conditional...` annotations: `@ConditionalOnClass` (does this class exist on the classpath?), `@ConditionalOnMissingBean` (have you already defined your own?), `@ConditionalOnProperty` (is a config flag set?), and more.

So `DispatcherServletAutoConfiguration` only activates because `spring-boot-starter-web` put `DispatcherServlet` on your classpath. If you define your own `DataSource` bean, `DataSourceAutoConfiguration` backs off entirely because of `@ConditionalOnMissingBean`. Nothing is truly automatic — it's a big set of "if this, then that" rules evaluated once, at startup.

{{< mermaid >}}
%%{init: {'flowchart': {'useMaxWidth': true}}}%%
flowchart TD
    A["SpringApplication.run(Main.class, args)"] --> B[Create ApplicationContext]
    B --> C["@ComponentScan registers your<br/>@Component / @Service / @Repository / @Controller beans"]
    C --> D["Auto-configuration import selector loads candidates from<br/>AutoConfiguration.imports"]
    D --> E{"Each candidate's<br/>@Conditional... annotations<br/>are evaluated"}
    E -- "Condition matches<br/>e.g. class found on classpath" --> F[Auto-config class registers its beans]
    E -- "Condition fails<br/>e.g. you already defined that bean" --> G[Auto-config class is skipped]
    F --> H[Context refresh completes]
    G --> H
    H --> I([Application is ready])

    classDef start   fill:#E6F1FB,stroke:#185FA5,color:#0C447C
    classDef scan    fill:#EEEDFE,stroke:#534AB7,color:#3C3489
    classDef auto    fill:#FAEEDA,stroke:#854F0B,color:#633806
    classDef applied fill:#E1F5EE,stroke:#0F6E56,color:#085041
    classDef skipped fill:#F1EFE8,stroke:#5F5E5A,color:#444441
    classDef done    fill:#FAECE7,stroke:#993C1D,color:#712B13

    class A,B start
    class C scan
    class D,E auto
    class F applied
    class G skipped
    class H,I done
{{< /mermaid >}}

## Why This Design Matters

This is Spring Boot's version of "convention over configuration": instead of you wiring up a `DataSource`, a `DispatcherServlet`, or a `JacksonObjectMapper` by hand, Spring Boot ships hundreds of pre-written `@AutoConfiguration` classes that quietly check "does this apply here?" and wire themselves in only when it makes sense. `@SpringBootApplication` is just the single switch that turns all three of these mechanisms — configuration, auto-configuration, and component scanning — on at once, which is exactly why removing it (or splitting it back into its three parts) is a perfectly valid, and sometimes clearer, thing to do once you understand what each piece is actually doing.
