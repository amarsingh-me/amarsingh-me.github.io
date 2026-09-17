---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-08-25
title: Dependency Injection and Inversion of Control
tags: [dependency-injection, inversion-of-control, spring, spring-boot, design-patterns]
categories: [Java]
---

Inversion of Control (IoC) is the principle that flips *who* controls object creation and program flow from your code to a framework/container. Dependency Injection (DI) is just one technique that implements IoC — specifically applied to how dependencies get created and handed to your classes.

## IoC vs DI

These are often used interchangeably, but IoC is the broader principle and DI is one specific flavor of it.

Without IoC, your class controls its own dependency creation:
```java
public class UserController {
    private UserService userService = new UserService(); // I create it myself
}
```
The class decides what to instantiate and when — it's "in control."

With IoC (via Spring), that control moves out of the class and into the container (`ApplicationContext`). The class just declares what it needs, and the container decides what to create and hands it over:
```java
@Controller
public class UserController {
    private final UserService userService;

    @Autowired
    public UserController(UserService userService) { // given to me, not created by me
        this.userService = userService;
    }
}
```
DI (constructor/setter/field injection) is the *mechanism* Spring uses to actually deliver the dependency once control has been inverted.

**IoC is broader than just dependency creation.** A classic way to describe it is the **Hollywood Principle**: *"Don't call us, we'll call you."* This shows up in Spring even outside of DI — you never call your `@Controller`'s method yourself; the `DispatcherServlet` calls it for you when a request arrives. That's IoC applied to *flow of control* (who invokes your code and when), as opposed to DI, which is IoC applied to *object creation*.

**IoC ≠ loose coupling.** Loose coupling (depending on an abstraction/interface rather than a concrete class) is a common *benefit* enabled by DI, but it's not the definition of IoC itself. You can still have IoC with tight coupling if you inject a concrete class instead of an interface — coupling is a separate axis from who controls creation/flow.

Summary of the mental model:
- **IoC** = who's driving (the framework decides what runs/gets created and when).
- **DI** = the specific case of IoC applied to handing your class its dependencies, instead of it constructing them itself.
