---
draft: false
weight: 10
showAuthor: true
showWordCount: true
showReadingTime: true
title: How to choose right collection in Java?
mermaid: true
---
Choosing the right Java collection can feel overwhelming. The standard library offers dozens of options across maps, sets, lists, and queues, each with different performance characteristics, ordering guarantees, and thread-safety trade-offs. Get it wrong and you are looking at subtle bugs, unexpected memory leaks, or performance bottlenecks under load. To cut through the noise, the decision tree below walks you through every major collection in the JDK, asking the right questions at each step so you always land on the best tool for your specific scenario.


{{< mermaid >}}
%%{init: {'flowchart': {'useMaxWidth': true}}}%%
flowchart LR
    START([What do you need to store?])

    START --> KV{Key-value pairs?}

    %% ── MAP BRANCH ──────────────────────────────
    KV -- Yes --> THREAD_MAP{Thread-safe?}

    THREAD_MAP -- Yes --> CHM[ConcurrentHashMap <br/>Lock-striped, high concurrency]
    THREAD_MAP -- No  --> ORDER_MAP{Order / sorting needed?}

    ORDER_MAP -- Sorted keys        --> TM[TreeMap<br/>NavigableMap, sorted by key]
    ORDER_MAP -- Insertion order    --> LHM[LinkedHashMap<br/>Predictable iteration order]
    ORDER_MAP -- No order needed    --> HM{Key type?}

    HM -- Enum keys    --> EM[EnumMap<br/>Fastest map for enum keys]
    HM -- Identity ==  --> IHM[IdentityHashMap<br/>Uses == not .equals]
    HM -- Weak refs    --> WHM[WeakHashMap<br/>Entries GC-eligible]
    HM -- General      --> HMP[HashMap<br/>Fastest general-purpose map]

    %% ── COLLECTION BRANCH ───────────────────────
    KV -- No --> DUPES{Allow duplicates?}

    %% SET sub-branch
    DUPES -- No, unique only --> SET_THREAD{Thread-safe?}

    SET_THREAD -- Yes --> COWAS[CopyOnWriteArraySet<br/>Thread-safe, small sets]
    SET_THREAD -- No  --> SET_ORDER{Order / sorting?}

    SET_ORDER -- Sorted          --> TS[TreeSet<br/>NavigableSet, sorted]
    SET_ORDER -- Insertion order --> LHS[LinkedHashSet<br/>Predictable iteration]
    SET_ORDER -- Enum values     --> ES[EnumSet<br/>Fastest set for enums]
    SET_ORDER -- No order        --> HS[HashSet<br/>Fastest general-purpose set]

    %% LIST / QUEUE sub-branch
    DUPES -- Yes, duplicates OK --> BEHAVIOR{Access pattern?}

    BEHAVIOR -- Indexed list     --> THREAD_LIST{Thread-safe?}
    BEHAVIOR -- Queue / Stack    --> QS{FIFO, LIFO, or Priority?}

    THREAD_LIST -- Yes, legacy  --> VEC[Vector / Stack<br/>Legacy, synchronized]
    THREAD_LIST -- Yes, modern  --> COWAL[CopyOnWriteArrayList<br/>Best for read-heavy]
    THREAD_LIST -- No, frequent get --> AL[ArrayList<br/>Fast random access]
    THREAD_LIST -- No, frequent insert/delete --> LL[LinkedList<br/>Fast head/tail ops]

    QS -- FIFO, no priority  --> BQ{Thread-safe?}
    QS -- FIFO + priority    --> PQ[PriorityQueue<br/>Min-heap, natural order]
    QS -- LIFO stack         --> ADS[ArrayDeque as Stack<br/>Preferred over Stack class]
    QS -- Bounded / blocking --> BLK[ArrayBlockingQueue<br/>LinkedBlockingQueue<br/>Producer-consumer]

    BQ -- Yes --> BQ2[LinkedBlockingQueue]
    BQ -- No  --> BQ3[ArrayDeque<br/>Fastest general queue]

    %% ── STYLING ──────────────────────────────────
    classDef question fill:#E6F1FB,stroke:#185FA5,color:#0C447C
    classDef map      fill:#E1F5EE,stroke:#0F6E56,color:#085041
    classDef setcls   fill:#EEEDFE,stroke:#534AB7,color:#3C3489
    classDef list     fill:#E1F5EE,stroke:#0F6E56,color:#085041
    classDef queue    fill:#FAEEDA,stroke:#854F0B,color:#633806
    classDef legacy   fill:#F1EFE8,stroke:#5F5E5A,color:#444441
    classDef conc     fill:#FAECE7,stroke:#993C1D,color:#712B13

    class KV,ORDER_MAP,HM,SET_ORDER,BEHAVIOR,QS,THREAD_MAP,THREAD_LIST,SET_THREAD,BQ,DUPES question
    class TM,LHM,HMP,EM,IHM,WHM map
    class TS,LHS,HS,ES setcls
    class AL,LL list
    class PQ,ADS,BQ3,BQ2 queue
    class BLK,CHM,COWAL,COWAS conc
    class VEC legacy
{{< /mermaid >}}
