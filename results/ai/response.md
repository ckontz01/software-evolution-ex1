# Guava JRE 33.7.2: conceptual architecture recovery

## Result and status

I propose **one architecture of 18 responsibility modules covering all 591 supplied canonical outer classes exactly once**. The assignment preserves the three classes with no incident edges and all other sparse types. `assignment.csv` is the definitive class-to-module mapping; `architecture.json` records exact counts, responsibilities, evidence, and interpretation. The release identification comes from the experiment inputs. This proposal is a human reading and maintenance-discussion map, not a claim to have recovered Guava's intended design or demonstrated a better architecture. [C, G]

The count of 18 follows the responsibilities I judged useful after inspecting the evidence. I did not select it to achieve a numerical graph score. I did not inspect baseline partitions, UE decisions, prior experiment reports, or quality outcomes, and did not compute MQ, cohesion, coupling, or another architecture-quality metric.

## Evidence and sequence

The permitted evidence consists of a 591-class manifest, 3,969 binary directed internal class dependencies, counts for 17 packages, 77 aggregated package-pair rows, and the supplied unmodified package documentation. Each graph edge means that its source class uses its target class. I verified that all 3,969 edges are unique, that their endpoints occur in the class manifest, and that aggregation by manifest package reproduces the supplied package dependency table. These are input-consistency checks, not architecture-quality evaluations. [C, G, K, P]

I first read only `classes.csv` and `package_counts.json`, after reading the task prompt. I then wrote `initial_hypothesis.md` before opening either dependency file or the documentation. The hypothesis described broad capabilities and explicitly deferred class allocation, the number of modules, collection/concurrency subdivisions, text boundaries, and helper ownership. It was not a second finalized architecture.

The additional evidence was inspected through Python summaries of class names, direct adjacency, package relationships, and sparse types, together with the full supplied package documentation. The final decisions were semantic judgments informed by those observations. Python then materialized the chosen memberships and checked coverage. Source-file paths in the manifest were visible, but I did not open those Java sources or follow documentation links.

Citation keys used below refer only to permitted files: **[C]** class manifest; **[G]** class dependencies; **[K]** package counts; **[P]** package dependencies; **[D: package]** the indicated package-info section of the supplied documentation. Their exact paths appear at the end.

## Final modules

| Stable module ID | Responsibility name | Classes |
|---|---|---:|
| `foundation` | Foundation and common contracts | 57 |
| `primitive_values` | Primitive values and arrays | 25 |
| `numeric_algorithms` | Arithmetic and statistics | 16 |
| `collections_core` | Core collections and shared collection machinery | 125 |
| `collections_multi` | Multimaps and counted collections | 59 |
| `collections_tables` | Tabular collections | 16 |
| `collections_ranges` | Intervals and bounded collections | 15 |
| `caching` | Caching and cache policy | 22 |
| `async_execution` | Futures and asynchronous execution | 57 |
| `service_lifecycle` | Service lifecycle management | 8 |
| `synchronization` | Synchronization and execution limits | 18 |
| `graph_model` | Graph models and traversal | 53 |
| `hashing` | Hashing and probabilistic structures | 33 |
| `io` | I/O, resources, and binary encodings | 37 |
| `escaping` | Escaping and format-specific escapers | 16 |
| `network_values` | Network and protocol values | 7 |
| `reflection` | Reflection and generic type modeling | 16 |
| `event_dispatch` | Event registration and dispatch | 11 |
| **Total** | **One complete partition** | **591** |

The four collection modules account for all 215 `collect` classes: 125 core, 59 multimap/multiset, 16 table, and 15 interval classes. The three concurrency modules account for all 83 `util.concurrent` classes: 57 asynchronous-execution, eight lifecycle, and 18 synchronization/control classes. Foundation combines `base`, `base.internal`, and the five shared annotation types. Escaping combines all `escape`, `html`, and `xml` classes with two classes from `net`. The other seven network classes remain together. [C, K]

## Why these boundaries are useful

### Foundation, basic text handling, and escaping

The initial names-only hypothesis entertained a larger text-processing area. The graph gives a reason to narrow that idea. `Preconditions` refers to both `Platform` and `Strings`; `Strings` refers back to both; and `Platform` also refers to `CharMatcher`, pattern infrastructure, `Enums`, and `Optional`. `Predicates` uses pattern and matching types. Basic strings, generic predicates, validation, and their platform implementation are interwoven at this class granularity. The base package has 117 internal edges and refers outside itself only to the shared annotations package and `base.internal`. [G, P]

I therefore retain the base classes in the foundation, including their text utilities. This is a conservative ownership judgment, not proof that a finer text boundary is impossible. Foundation also contains the reference-cleanup family: `FinalizableReferenceQueue -> base.internal.Finalizer` is the latter class's only incident edge. Its name, placement, and concrete consumer agree on that owner. [C, G]

The evidence for combining format-specific escapers is more direct. The escape documentation explicitly identifies the HTML, XML, and URL implementations as members of the escaper family. `HtmlEscapers` and `XmlEscapers` each refer to `Escaper` and `Escapers`; `PercentEscaper` refers to `UnicodeEscaper`; and `UrlEscapers` refers to `Escaper` and `PercentEscaper`. None of the remaining network classes refers to either moved URL class. This supports a 16-class escaping responsibility spanning four packages. [G; D: escape, html, xml]

The distinction is functional: basic string operations remain common support; the escaping module owns transformations expressed through the escaper abstraction. `BaseEncoding` stays in I/O because its graph references the byte/character source and sink types. That class has no reference to the escape package. A shared word such as “encoding” is insufficient to combine these different interfaces. [G]

### Four collection responsibilities, with shared machinery acknowledged

The collection documentation describes multiple data models rather than a single undifferentiated container API. It distinguishes multi-valued maps, counted collections, paired-key tables, intervals, immutable variants, forwarding adapters, and general utilities. That makes it a useful source of responsibility vocabulary, though it does not validate my chosen boundaries. [D: collect]

**Core collections** retains lists, sets, ordinary and bidirectional maps, iteration, ordering, raw class-to-instance maps, interning, decorators, and shared implementation support. Interfaces and their immutable variants stay together: for example, `ImmutableList` refers to `ImmutableCollection`, `RegularImmutableList`, and `SingletonImmutableList`. A separate “immutable collections” module would span several distinct collection contracts, because the documentation expressly provides immutable versions of both JDK-style and Guava-specific collection types. I use responsibility, rather than mutability, as the primary partition axis. [G; D: collect]

**Multimaps and counted collections** joins 35 multimap-family classes with 24 multiset-family classes. This is more than a shared naming pattern: there are 19 direct multimap-to-multiset edges. `Multimap` itself refers to `Multiset`; `ImmutableMultimap` refers to `ImmutableMultiset`, `Multiset`, and `Multisets`; and `Multimaps` refers to multiset abstraction and utility classes. None of the 24 selected multiset-family classes refers to the 35 multimap classes. I interpret the common multiplicity contracts and this reuse as a practical reason to give them one owner at this level of detail. `Count` follows its sole observed consumer, `AbstractMapBasedMultiset`. [C, G]

**Tabular collections** contains the 16 classes for values addressed by row and column keys. The documented two-key data model differs from ordinary and multi-valued maps. Its representation and adapter names align with concrete references: `ImmutableTable` uses `Table`, `AbstractTable`, regular/singleton/sparse variants, `TableCollectors`, and `Tables`. The two incoming references to `TableCollectors` are from `ImmutableTable` and `Tables`, which supports keeping that helper with tables. [G; D: collect]

**Intervals and bounded collections** contains 15 classes for bounds, discrete domains, contiguous sets, range sets, and range maps. `Range` refers to `BoundType`, `Cut`, and `DiscreteDomain`; the tree and immutable range representations connect to these same concepts. This matches the separate range family in the documentation. `GeneralRange` also refers to `Range` and `BoundType`, so I place it here. However, its sole observed caller is `TreeMultiset`. That is a real alternative ownership cue and makes this particular placement less certain than the broad interval responsibility. [G; D: collect]

These four modules are **not an established one-way hierarchy**. `CollectCollectors`, `Synchronized`, and `Serialization` span families and receive one owner in core collections. `CollectCollectors` has 15 incoming class references, including ordinary immutable collections, multimaps/multisets, and immutable range types. `Synchronized` is used by `Maps`, `Multimaps`, `Queues`, `Sets`, and `Tables`. `Serialization` has 12 incoming class references, including both bidirectional maps and multiplicity collections. Moreover, core `Maps` and `Sets` refer to `Range` and `BoundType`. These observations expose shared machinery and references in both directions; they do not invalidate a conceptual reading map or establish that these groups can become independent build artifacts. [G]

The remaining 125-class core is deliberately broad. I have not treated its size as a score to minimize. A finer division among collection implementation, ordering, and iteration would need more evidence about member-level use, API visibility, and intended ownership than these inputs provide.

### Three concurrency responsibilities

The initial hypothesis identified futures, executors, service lifecycles, locks, atomics, and limits from names. The package documentation calls out `ListenableFuture`, `ClosingFuture`, and `Service`, along with executor and waiting utilities. The graph supports distinguishing those responsibilities while making their shared support explicit. [C; D: util.concurrent]

**Futures and asynchronous execution** keeps future composition with listening executors and task adapters. For example, `Futures` refers to `MoreExecutors` and `ListenableFuture`, while `MoreExecutors` refers to `AbstractFuture`, `ListenableFuture`, listening-executor interfaces, and `TrustedListenableFutureTask`. This is a reason not to separate “futures” and “executors” solely on their names. The 57 classes also include shared package support such as `Internal`, `Platform`, `LazyLogger`, and nullness helpers. Their assignment is a single-owner convention, not a claim that only asynchronous code uses them. [G]

**Service lifecycle management** contains eight classes. There are 13 edges among these classes and no incoming edge from outside that family in the supplied internal graph. The templates use `AbstractService` and `Service`; `ServiceManager` refers to the service abstractions and its bridge; and the two observed callers of `ListenerCallQueue` are `AbstractService` and `ServiceManager`. I interpret this as a recognizable lifecycle feature that consumes execution and synchronization services. The absence of other internal callers says nothing about application use, because application consumers are excluded. [G]

**Synchronization and execution limits** contains 18 classes covering atomics, locks/conditions, monitors, blocking-collection adapters, rate/time limits, and interruption-tolerant waits. Its boundaries are somewhat broader and less certain than the lifecycle family. Nevertheless, the characteristic relations fit: `Striped` uses `ForwardingCondition` and `ForwardingLock`; `RateLimiter` and `SmoothRateLimiter` refer to each other; and `SimpleTimeLimiter` uses `TimeLimiter`, `UncheckedTimeoutException`, and `Uninterruptibles`. Some atomic classes have few internal references because their external/JDK relationships are outside this evidence. Sparse internal structure is not a reason to discard their recognizable responsibility. [C, G]

`Monitor` could plausibly follow its two observed lifecycle callers, but its general synchronization role leads me to put it in controls. `Uninterruptibles` also receives one control owner despite its six callers spanning caches, futures, adapters, and limiters. Shared `Internal` and `LazyLogger` remain in asynchronous execution even though services and controls use them. These are explicit judgments that a maintainer should review. They create cross-boundary references, including in both directions, and I do not claim to have discovered three separately deployable concurrency components. [G]

### The remaining capability areas

**Primitive values and arrays** and **arithmetic and statistics** become separate modules after being tentatively considered together. The documentation distinguishes per-type representations, unsigned values, and immutable arrays from arithmetic functions. The graph contains five math-to-primitives edges and none in the reverse direction: `IntMath -> Ints`, `LongMath -> UnsignedLongs`, `PairedStatsAccumulator -> Doubles`, and `Quantiles -> Doubles` and `Ints`. Statistics are additionally evidenced by names and the accumulator relationships: `StatsAccumulator` refers to `Stats`, and `PairedStatsAccumulator` refers to the paired statistics and linear-transformation types. This supports representation and numerical algorithms as different responsibilities without asserting a universal runtime layering rule. [G, P; D: primitives, math]

**Caching** remains a 22-class feature because loading, cache policy, removal, and statistics are more specific responsibilities than ordinary maps or task execution. `CacheBuilder` connects to its cache APIs and `LocalCache`, while `LocalCache` connects to entry and removal-policy types. Its use of futures is a collaborator relationship: the cache package has 11 edges to concurrency classes, including three from `CacheLoader` to future APIs and task implementations. I do not relocate caches into asynchronous execution on that basis. [G, P; D: cache]

**Graph models and traversal** keeps the 53 graph classes together. The documentation identifies a graph-data API analogous to collection APIs, and the builders connect to the corresponding graph/value-graph/network interfaces and implementations. The 65 references from graph classes to collection classes show implementation reuse. They do not erase the graph responsibility. Similarly, `collect.TreeTraverser` stays in core collections: its observed internal references are to collection iteration and fluent-iteration types, with no graph-package dependency. [G, P; D: graph]

**Hashing and probabilistic structures** keeps hash functions, funnels, Bloom filters, and hashing stream wrappers together. Both `HashingInputStream` and `HashingOutputStream` refer to `HashCode`, `HashFunction`, and `Hasher`, with no I/O-package dependency. Their stream-shaped API does not outweigh that operation-specific role. **I/O, resources, and binary encodings** follows the documented source/sink abstractions; byte and character source/sink classes, readers/streams, files, resource management, and base encodings remain together. I/O uses hashing and graph traversal: its package graph has seven references to hashing and four to graph classes. Those four are the references from `Files` and `MoreFiles` to `SuccessorsFunction` and `Traverser`. [G, P; D: hash, io]

**Network and protocol values** contains the seven network classes left after assigning URL escapers. `HostSpecifier` uses the host/port, address, and domain abstractions. `MediaType` uses both ordinary collections and multimap/multiset classes, yet its responsibility remains protocol-value handling. `InetAddresses` uses three hashing types and two I/O types; these are useful navigation links rather than reasons to merge three capabilities. [G; D: net]

**Reflection and generic type modeling** retains all 16 reflection classes. `TypeToken` connects to capture, parameter, resolver, visitor, representation, and invocation types; `ClassPath` accounts for the three reflection-to-I/O edges. Raw `ClassToInstanceMap` variants remain in core collections. Their names alone do not require combining them with `TypeToInstanceMap`, and the supplied graph has no collect-to-reflect edge. **Event registration and dispatch** retains 11 classes with its dispatcher, registry, subscriber, and exception family. `SubscriberRegistry` uses three cache types and `TypeToken`; `EventBus` uses `MoreExecutors`. That is consistent with a higher-level communication capability composed from other utilities, although these type edges do not reveal runtime event flow. [G, P; D: reflect, eventbus]

The cache and EventBus documentation recommends alternatives. I record that as documentation context only. Recovery must still explain the supplied classes, and a recommendation about API choice is not evidence that a capability should be omitted or merged. [D: cache, eventbus]

## How the additional evidence changed the initial hypothesis

The initial capability vocabulary mostly survived, but the final partition is more specific. Collections changed from one unresolved area into four responsibilities, supported by documented data models and concrete family relations. Concurrency became three areas, with a narrowly identifiable service family and explicit ownership for shared support. The tentative broad text area was narrowed: base text helpers stay with foundation, while the documentation and graph support joining URL, HTML, XML, and generic escaping. Primitive utilities and numerical algorithms became separate areas after their distinct documented roles and dependency direction were inspected.

Other names-only expectations were confirmed with qualifications. Graphs, caches, hashing, I/O, reflection, and events are identifiable capabilities, but their collaborators are now explicit. Similar names were not sufficient for relocation: hashing streams remain with hashing, raw class-to-instance maps with core collections, and collection traversal with collections. Low-degree helpers and annotations gained definite owners, while uncertainty about those choices remains documented. This comparison concerns a qualitative hypothesis and one final assignment, not two evaluated partitions.

## Package bias and confidence

**Package structure influenced my reasoning.** It supplied the first organizing prior, and much of the documentation uses the same organization. Many final modules retain whole packages. Class names and prior familiarity with standard Java/Guava vocabulary can also affect interpretation. This procedure is therefore not a package-blind or prior-knowledge-free recovery method, even though no outside information was retrieved.

I challenged that prior where both responsibility and graph evidence supported doing so: four collection groups, three concurrency groups, and the escaper family crossing package boundaries. Those changes demonstrate that the result is not merely a package assignment; they do not demonstrate that package bias was eliminated or that my alternatives are correct. Remaining small support annotations generally follow package context because their names and sparse references provide little better evidence.

Confidence is strongest in broad documented roles and direct interface/implementation-family connections. It is moderate in the exact collection and concurrency subdivisions. It is lower in helper ownership, the breadth of the synchronization group, and any claim about intended team, build, or release boundaries. In particular, the graph does not establish whether `GeneralRange` should belong with interval semantics or its observed `TreeMultiset` consumer, whether `Monitor` should follow lifecycle callers, or where package-wide shared utilities should be owned.

## Limits and maintainer validation

The graph gives one binary directed edge per class pair. It does not quantify call frequency, runtime importance, or maintenance effort. Its two-column format does not distinguish annotations, inheritance, field types, signatures, and member uses. For example, the 330 incoming references to `GwtCompatible` are visible metadata relationships, not evidence of 330 runtime service calls. The 312 incoming references to `Preconditions` likewise describe graph presence, not execution volume. [G]

External dependencies and consumers are excluded. Dynamic/reflection-mediated completeness cannot be established from this table. Inner and anonymous classes have been merged into outer classes, so broad helpers such as `Synchronized` and `CollectCollectors` cannot be split by individual adapter or method. This limitation materially affects single ownership across collection responsibilities. Documentation varies in detail and states package-level descriptions, not verified ownership rules. No Java method bodies, history, issue records, or maintainer interviews were examined.

A maintainer would need to validate:

- Whether these responsibilities match intended API and maintenance ownership.
- Whether shared collectors, serializers, synchronization wrappers, concurrency support classes, and annotations should have the owners chosen here.
- Whether `GeneralRange`, `Monitor`, and `Uninterruptibles` should follow semantic roles or their particular consumers.
- Whether immutability is an intended independent architectural concern rather than a variant within each collection abstraction.
- Whether lifecycle and execution controls are intended subsystems, and whether any conceptual boundary could become a compilation or release boundary without compatibility, visibility, or performance changes.
- Which historical intentions and current maintenance practices explain the documented recommendations for cache and EventBus alternatives.

I make no superiority claim relative to clustering algorithms, no architectural-accuracy claim without ground truth, and no measured maintainability claim. Reciprocal references across proposed modules remain visible, and physical modularization would be a separate task.

## Coverage and value for a human reader

The produced CSV has exactly the two requested columns, one row per supplied class, no duplicate class assignment, no invented class, and no omitted class. Module counts in the JSON were checked against the actual CSV and sum to 591. The isolated types are `cache.IgnoreJRERequirement`, `math.IgnoreJRERequirement`, and `reflect.AbstractInvocationHandler`; they remain in caching, numerical algorithms, and reflection respectively. Types with a single graph relationship, such as `base.internal.Finalizer`, `net.HttpHeaders`, and `util.concurrent.Runnables`, are also preserved. [C, G]

The proposal helps a reader find code by the responsibility involved: a table change has a concrete 16-class family; a service-lifecycle change has an eight-class family and explicit executor/monitor collaborators; an escaping change has one map across four packages. Shared helpers are identified once, so the map also exposes where a change may need discussion across responsibilities. That is its practical contribution: a complete, named, evidence-linked starting point for understanding and maintainer review, with uncertainty and cross-boundary dependencies retained.

## Evidence paths

- **[C]** `results/ai/inputs/classes.csv`
- **[G]** `results/ai/inputs/dependencies.csv`
- **[K]** `results/ai/inputs/package_counts.json`
- **[P]** `results/ai/inputs/package_dependencies.csv`
- **[D]** `results/ai/inputs/package_documentation.txt`; section names refer to the `FILE com/google/common/.../package-info.java` markers in that supplied file.

The task instructions were read from `results/ai/prompt.txt`. The evidence-order record is `results/ai/initial_hypothesis.md`, and the input/method/identity declarations and coverage checks are recorded in `results/ai/activity.json`.
