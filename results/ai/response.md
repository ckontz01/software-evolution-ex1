# Recovered conceptual architecture: Guava 33.7.2 JRE

## Result and status

This proposal assigns **all 594 supplied canonical outer types to exactly one of 18 named responsibility modules**. It includes the Guava-owned public-suffix implementation, all 31 annotation declarations, and every isolated type. `assignment.csv` is the definitive flat partition; `architecture.json` contains the module definitions, observations, rationale, and limitations. The module count is a practical choice for explaining responsibility, not a target selected from a clustering score. [C] [A]

The result is a conceptual map for human review. It is not a claim about Guava's official intended architecture, an immediately extractable set of Java modules, or a demonstrated improvement over another recovery method. No architectural ground truth was supplied. Package names, package documentation, and the supplied class dependencies are evidence with different strengths, and the rationale below distinguishes observations from interpretation.

## Evidence, scope, and procedure

The experiment prompt identifies the selected release as 33.7.2 JRE. I first read only `classes.csv` and `package_counts.json` and saved `initial_hypothesis.md`. Only after that checkpoint did I inspect `dependencies.csv`, `package_dependencies.csv`, and the unmodified matching-source package documentation. I did not inspect class implementations, follow documentation links, browse external sources, consult baseline partitions or UE decisions, or inspect quality scores or other experiment reports.

The inventory contains 594 unique classes across 18 packages, where “class” in the assignment includes outer classes, interfaces, enums, and annotation declarations. The dependency file contains 2,750 unique directed internal edges, with no unknown endpoints or self-edges. A source uses a target's type/member; these are binary relationships, not call-frequency measurements. The 64 supplied package-edge records aggregate to the same 2,750 edges, and package counts agree with the inventory. These are input consistency checks, not architecture quality measures. [C] [D] [P] [PD]

Python was used to read the permitted evidence, list names by package, inspect outgoing and incoming relationships for candidate responsibilities, confirm package aggregation, construct one explicit class assignment, and validate its coverage. There was no clustering algorithm, metric search, MQ calculation, cohesion/coupling calculation, or comparison with another partition. The staged checkpoint and exact input paths are recorded in `activity.json`.

## Final module map

Counts below are canonical outer-type counts in the final assignment. They do not measure code size or maintenance effort. Responsibility statements are this reviewer's interpretations of the evidence. [C] [A]

| Stable ID | Responsibility module | Classes | Scope |
|---|---|---:|---|
| `foundation` | Core values and programming contracts | 57 | Basic values, argument checks, functional adapters, text helpers, timing, reference lifecycle support, and shared API/platform annotation declarations. |
| `collections_core` | Core collections and ordering | 127 | Ordinary maps, bimaps, lists, sets and queues; immutable implementations of those types; collection views, iteration, ordering, forwarding decorators, interning, and shared collection support. |
| `multimaps_multisets` | Multimaps and multisets | 59 | Multiple-value mappings and occurrence-counting collections, including their interfaces, mutable and immutable implementations, filtering views, sorted variants, and dedicated forwarding adapters. |
| `tables` | Two-dimensional tables | 16 | Row/column-keyed Table APIs, mutable and immutable representations, forwarding views, and table-specific collectors. |
| `ranges` | Ranges and interval collections | 15 | Range endpoints and bounds, discrete domains, contiguous sets, and range-set/range-map representations. |
| `caching` | Caching and removal policy | 22 | Cache APIs, loading, construction and configuration, eviction/removal policy, statistics, and local cache implementation support. |
| `async_execution` | Futures and execution runtime | 58 | Future values and composition, listening executors, task submission and sequencing, executor adapters, thread factories, execution exceptions, interrupt/wait helpers, and shared runtime support. |
| `service_lifecycle` | Service lifecycle management | 8 | Service state/lifecycle APIs, service implementation templates, service groups, and lifecycle listener dispatch. |
| `synchronization_limits` | Synchronization and execution limits | 15 | Atomic state utilities, locks and monitors, striped/cycle-detecting synchronization, rate limiting, and time limits. |
| `graphs` | Graph models and traversal | 53 | Graph, network and value-graph APIs, builders, mutable/immutable representations, adjacency/connection machinery, and traversal. |
| `hashing` | Hash functions and probabilistic membership | 33 | Hash functions and codes, hashers, primitive sinks/funnels, digest and checksum adapters, hashing streams, and Bloom filters. |
| `io_resources` | Streams, files and resource I/O | 37 | Byte/character sources and sinks, streams and readers, file/resource operations, resource closing, line processing, and base encoding. |
| `primitive_values` | Primitive value utilities | 25 | Primitive-type utilities and conversions, unsigned value types, immutable primitive arrays, and associated platform helpers. |
| `mathematics` | Arithmetic and statistics | 16 | Arithmetic and rounding over numeric values, quantiles, statistical summaries/accumulators, and linear transformations. |
| `network_values` | Network identifiers and protocol values | 10 | IP addresses, host/port specifications, domain names and owned public-suffix support, media types, and HTTP constants. |
| `text_escaping` | Text escaping policies | 16 | Generic character/Unicode escape abstractions, escaper builders, and HTML, XML, and URL escaping policies. |
| `reflection` | Reflection and generic types | 16 | Generic type capture/resolution, type tokens, invocation and parameter inspection, type-to-instance maps, class-path inspection, and reflection helpers. |
| `event_dispatch` | Event subscription and dispatch | 11 | Event bus APIs, synchronous/asynchronous dispatch support, subscription declarations, subscriber discovery, and exception handling. |

### What crosses package boundaries

The assignment contains several deliberate departures from a package partition. Core values and programming contracts combines 51 `base` types, the single `base.internal.Finalizer`, and five shared annotation declarations. The collection package becomes 125 core types, 59 multimap/multiset types, 16 table types, and 15 range types. The core collection module also receives two blocking forwarding adapters from `util.concurrent`, bringing its final count to 127. [C] [A]

The concurrency package contributes 58 types to futures/execution, eight to service lifecycle, and 15 to synchronization/limits, with the two forwarding adapters accounted for above. Text escaping combines ten `escape` types, two `html` types, two `xml` types, and `net.PercentEscaper` plus `net.UrlEscapers`. Network values contains the other seven `net` types and all three public-suffix types. No class is copied into more than one module. [C] [A]

## Why these boundaries are useful

### A shared foundation, with text helpers retained

**Observation.** The base package documentation explicitly groups strings, function types, and other basic utilities. The graph shows reciprocal relationships between `Preconditions` and `Strings`; `Preconditions` uses `Platform`, while `Platform` uses `CharMatcher`, `Enums`, `Optional`, and `Strings`. `FinalizableReferenceQueue` directly uses `base.internal.Finalizer`. There are 106 base-to-base edges and one base-to-base.internal edge; `Preconditions` has 312 incoming class edges across the supplied graph. [DOC: base] [D] [PD]

**Interpretation.** These relationships favor keeping the basic checks, values, text helpers, and platform support together at this level of explanation. The names-only hypothesis left open a separate base text responsibility. The added evidence made that boundary less persuasive: checks and text/platform behavior already refer to one another. Reference lifecycle support stays with its public base family, and the five shared annotation declarations receive a home with programming contracts. Their ownership is a semantic judgment because the graph has no annotation-use edges.

### Four collection responsibilities, with visible shared mechanics

**Observation.** `collect` has 215 supplied types and 1,128 same-package relationships. Its documentation describes several distinct contracts as well as immutable implementations, ordinary collection utilities, iterators, forwarding wrappers, and ranges. It explicitly says immutable implementations cover both JDK collection types and Guava-specific types. [C] [P] [PD] [DOC: collect]

**Interpretation.** A single collection module would conceal useful differences in data semantics. I therefore separate ordinary containers and mechanics, multivalue/counting containers, two-dimensional tables, and interval collections. I retain immutable implementations with the contract they implement: `ImmutableTable` belongs to tables, `ImmutableMultiset` to multimap/multiset behavior, and `ImmutableRangeSet` to ranges. This avoids making the `Immutable` name prefix the sole ownership rule.

**Observation.** `Multimap` uses `Multiset`, and so do `AbstractMapBasedMultimap` and `ImmutableMultimap`. `ImmutableMultimap` also uses `ImmutableMultiset`, `ImmutableList`, and `ImmutableMap`. `AbstractMapBasedMultiset` uses `Count`. In the table family, `StandardTable` references `AbstractTable`, `Table`, and `Tables`; only `ImmutableTable` and `Tables` reference `TableCollectors`. The documented range family is reflected by `Range` using `BoundType`, `Cut`, and `DiscreteDomain`, and by contiguous/range-map/range-set implementations referring to those concepts. [D] [DOC: collect]

**Interpretation.** These are specific reasons to keep multimap and multiset implementations together, make table collection/representation behavior a separate area, and assign endpoint/bound semantics to ranges. `GeneralRange` is a difficult boundary case: it uses `Range` and `BoundType`, but its only recorded incoming source is `TreeMultiset`. I place it with range semantics while recording the multiset dependency. A maintainer might reasonably prefer a different ownership choice after reading the implementation.

**Observation.** Collection mechanics do not form a strictly independent lower layer. `CollectCollectors` references ordinary, multivalue, and range containers. `Synchronized` is used by `Maps`, `Multimaps`, `Queues`, `Sets`, and `Tables`, and refers to several of their contracts. `ImmutableMap` uses `ImmutableSetMultimap`, while `ImmutableMultimap` uses `ImmutableMap`. `Maps` and `Sets` use range types, and range types use ordinary collections and ordering. `Serialization` has consumers among both bimaps and multimap/multiset implementations. [D]

**Interpretation.** `CollectCollectors`, `Synchronized`, and `Serialization` have one explicit home in the collection core. The result contains references in both directions between collection responsibilities. This is acceptable for a conceptual ownership map but is a concrete reason not to treat it as a ready-made physical module extraction. Package-private access and API compatibility would require a source-level review that is outside the permitted evidence.

The two `util.concurrent` blocking forwarding adapters also join the collection core. Both `collect.ForwardingBlockingDeque` and `util.concurrent.ForwardingBlockingDeque` directly use `collect.ForwardingDeque`, while `util.concurrent.ForwardingBlockingQueue` uses `collect.ForwardingQueue`. This supports grouping their container-delegation role with the existing collection decorators. It does not establish that the two deque types are aliases. [D]

### Execution, service lifecycle, and coordination

**Observation.** The concurrency documentation highlights `ClosingFuture`, `ListenableFuture`, `Service`, `Futures`, and `MoreExecutors`. `Futures` connects directly to future-catching, transformation, aggregation, and timeout implementations. `MoreExecutors` connects listening-executor APIs to task implementations. `AbstractFuture` and `AbstractFutureState` refer to one another. [DOC: util.concurrent] [D]

**Interpretation.** Future state, future composition, executors, task sequencing, and executor adapters belong together in the execution runtime. I retain shared helpers such as `LazyLogger`, `Internal`, `Platform`, and `Uninterruptibles` there, with one assignment per helper. Their callers from other responsibilities are dependencies rather than reasons to duplicate the helpers.

**Observation.** The three service templates use `AbstractService` and `Service`. `ServiceManager` uses those lifecycle types, `ServiceManagerBridge`, `ListenerCallQueue`, and `Monitor`. `ListenerCallQueue` and `Monitor` each have exactly two incoming sources, `AbstractService` and `ServiceManager`. `Striped` instead uses `ForwardingCondition` and `ForwardingLock`; `RateLimiter` and `SmoothRateLimiter` refer to one another; the two time-limiter implementations use `TimeLimiter`. [D]

**Interpretation.** Service state and lifecycle callbacks receive an eight-type responsibility, including `ListenerCallQueue`. Atomic values, monitor/lock coordination, and rate/time limits form a separate practical group. `Monitor` is placed there because a monitor is a reusable coordination concept, despite its current observed lifecycle consumers. That distinction comes from semantic interpretation, not from an algorithm proving a unique boundary. Service and coordination types use the execution runtime through helpers, executors, exceptions, and waiting support.

The smaller coordination concerns remain one module instead of becoming separate modules for atomics, locks, rate limits, and time limits. Conversely, the large future/executor implementation remains together because its interfaces and implementations directly collaborate. The chosen granularity is intended to make review and navigation manageable; no optimum is asserted.

### Cross-package escaping and domain-name support

**Observation.** The escape package documentation explicitly identifies HTML, XML, and URL escapers as additional implementations. `HtmlEscapers` and `XmlEscapers` each use `Escaper` and `Escapers`; `PercentEscaper` uses `UnicodeEscaper`; `UrlEscapers` uses `Escaper` and `PercentEscaper`. The package graph records six combined html/xml/net-to-escape edges. [DOC: escape, html, xml] [D] [PD]

**Interpretation.** This confirms the initial cross-package escaping hypothesis. These implementations form one text-escaping responsibility even though the source package organization locates policies near their application domain. Base string manipulation and I/O base encoding remain separate responsibilities because their documentation and observed collaborators support those distinctions.

**Observation.** `InternetDomainName` directly references `PublicSuffixPatterns`, `PublicSuffixTrie`, and `PublicSuffixType`, accounting for all three net-to-publicsuffix relationships. `PublicSuffixPatterns` uses `PublicSuffixTrie`, which uses `PublicSuffixType`. All three are supplied owned types, despite the `thirdparty` namespace. [C] [D] [PD]

**Interpretation.** Public-suffix support belongs with domain-name interpretation in the network-values module. This confirms the tentative names-only hypothesis and prevents a namespace label from excluding owned implementation types. The supplied documentation has no separate public-suffix section, so this placement rests primarily on the inventory and concrete relationships.

### Primitive representation and numerical computation

**Observation.** Primitive documentation describes per-type utilities, unsigned values, and immutable arrays; mathematics documentation describes arithmetic over primitives and big-number values. Five edges go from math to primitives: `IntMath` to `Ints`, `LongMath` to `UnsignedLongs`, `PairedStatsAccumulator` to `Doubles`, and `Quantiles` to `Doubles` and `Ints`. The reverse direction has no edge in the supplied graph. [DOC: primitives, math] [D] [PD]

**Interpretation.** The evidence resolves the initial broad numeric area into two responsibilities. Primitive values owns representation, conversion, and storage; mathematics owns arithmetic, rounding, quantiles, and statistical behavior. Immutable primitive arrays stay with primitive values rather than joining object collections. This observed direction supports the proposed distinction but does not prove a permanent architectural rule.

### Other facilities keep clear identities while using common services

**Observation.** Graph documentation describes node/edge APIs, and `Graphs` refers to graph, network, value-graph, and traversal families. Hashing connects concrete functions, hash codes, hashers, and funnels; `BloomFilter` and `BloomFilterStrategies` refer to one another and to those hash abstractions. I/O documentation names the four source/sink types as its core, and `BaseEncoding` directly uses all four. `TypeToken` uses the type-capture, resolver, visitor, invocation, and `Types` machinery. [DOC: graph, hash, io, reflect] [D]

**Interpretation.** These observations confirm the provisional graph, hashing, I/O, and reflection responsibilities. A facility keeps the implementation that expresses its behavior even when it composes other facilities. `HashingInputStream` remains with hashing, `ClassPath` remains with reflection, and `BaseEncoding` remains with I/O. `collect.Hashing` stays with collection mechanics: a shared short name is not sufficient evidence that it belongs with `hash.Hashing`.

**Observation.** `LocalCache` uses futures/execution support, and the package graph records 11 cache-to-concurrency edges. `SubscriberRegistry` uses `CacheBuilder`, `CacheLoader`, `LoadingCache`, and `TypeToken`; `EventBus` uses dispatch and subscriber machinery. `Files` and `MoreFiles` each use `Traverser` and `SuccessorsFunction`, giving four I/O-to-graph edges. `ClassPath` uses `ByteSource`, `CharSource`, and `Resources`, giving all three reflection-to-I/O edges. [D] [PD]

**Interpretation.** Caching, event dispatch, files, and class-path discovery are composite responsibilities. A reader can follow those explicit collaborator relationships without treating collaborators as part of every consumer's module. The package documentation marks cache and eventbus APIs as discouraged. That is useful status evidence, but it neither removes their maintenance responsibility nor authorizes dropping their supplied types from recovery. [DOC: cache, eventbus]

## How the added evidence changed the initial hypothesis

The checkpoint proposed responsibility areas without giving a finalized class partition or fixing a module count. The final design refines it in the following ways:

1. **Collections became four responsibilities.** The names suggested possible subareas; documentation supplied their contract semantics, and the graph supplied concrete implementation links and shared-helper limitations.
2. **Concurrency became three responsibilities.** Future/executor relationships, lifecycle-template links, and dedicated coordination families supported the split. Two forwarding container adapters crossed into the collection core.
3. **Primitives and mathematics separated.** Different documented purposes and the observed dependency direction clarified their different roles.
4. **Base text stayed in the foundation.** Reciprocal check/string/platform relationships argued against introducing another conceptual boundary inside base for this proposal.
5. **Escaping and public-suffix placement were confirmed.** Explicit documentation plus dependencies supported the cross-package escaping group; domain-name dependencies supported owned suffix inclusion.
6. **Caching, graphs, hashing, I/O, reflection, and event dispatch remained recognizable areas.** Added evidence explained their collaboration rather than requiring their consumers or dependencies to be merged.
7. **Isolation became an explicit confidence limit.** All isolated types were preserved, but their placement was not treated as graph-supported evidence of intended ownership.

These changes are refinements of one initial qualitative hypothesis into one final partition. They are not a comparison of two finalized architectures.

## Package bias and confidence limits

Package structure strongly influenced the initial vocabulary and still influences the result. Most small, recognizable packages remain intact; default placement of local support and annotation types follows their surrounding family. The docs themselves describe the current package organization, so they are not an independent validation of intended conceptual boundaries. Splitting collections and concurrency, combining the escaping packages, incorporating public-suffix support, and moving the two blocking adapters demonstrate that package equality was not enforced. They do not eliminate package bias.

There are **45 isolated vertices: all 31 annotation declarations and 14 other types**. Examples include `Charsets`, `Flushables`, `HttpHeaders`, `AbstractInvocationHandler`, and `Atomics`. These remain assigned. The supplied graph deliberately excludes annotation applications, so the absence of edges around `Subscribe` and `AllowConcurrentEvents` says nothing about their importance to event semantics. Similarly, no-edge utility or constant types can still be used by external clients outside this internal graph. [C] [D]

Semantic confidence is comparatively stronger for the documented escaping group, the domain/public-suffix relationships, and named container/type families with direct implementation connections. Confidence is lower for the exact grouping size, ambiguous package-local support, annotations, `GeneralRange`, and whether reusable `Monitor` ownership should follow its two current consumers. `Partially`, for example, has no supplied edge and receives a local execution-runtime default; the evidence does not justify a detailed claim about its purpose. [C] [D]

The graph is static, binary, directed, internal, and normalized to outer types. Inner/anonymous implementation detail is merged; external libraries are absent. The evidence does not establish runtime interaction, reflection targets, resource coupling, annotation/build behavior, change frequency, team ownership, or API usage by clients. Zero observed reverse edges or zero degree is a property of this evidence scope, not a universal behavioral claim. The supplied documentation also omits separate sections for `base.internal` and `publicsuffix`.

## Intended-design claims that require maintainer validation

Maintainers would need to validate whether these responsibility boundaries match how they reason about changes and ownership, especially the four collection areas and the service/coordination split. They would also need to assess whether immutable implementation sharing and helpers such as `CollectCollectors`, `Serialization`, `Synchronized`, `Internal`, and `LazyLogger` are best understood as shared mechanisms in the chosen homes or as evidence for different boundaries.

Any claim that these conceptual modules could become separately compiled, released, or versioned units needs source, visibility, build, and compatibility review. The reciprocal collection relationships already show why the partition alone cannot establish that claim. The placement of isolated annotations and ambiguous support classes needs declaration/source context, while `GeneralRange` and `Monitor` need design-level discussion about domain ownership versus observed consumers. Finally, maintainers must confirm whether a single-release static view captures intended future direction, particularly for APIs that package documentation discourages.

## How this helps a human understand Guava

The proposal gives each supplied type one navigable conceptual home. A reader looking for a range operation can begin with interval semantics, while a reader investigating service state can begin with lifecycle APIs and then follow explicit dependencies to monitors and executors. The collection split identifies differences between key/value maps, multiplicity, row/column addressing, and interval behavior without hiding the shared collection machinery.

The cross-package groups are especially useful for finding a whole responsibility: escaping includes its HTML/XML/URL implementations, and domain-name handling includes the owned suffix implementation. Conversely, the dependency observations explain why a cache involves futures, subscriber discovery involves cache/type utilities, and file traversal involves graph APIs. These relationships support human navigation and focused review. They do not, on their own, predict maintenance effort or prove that a change will remain inside one module.

## Validation and evidence references

Coverage validation passed for the serialized assignment: **594 rows, 594 distinct supplied classes, zero missing classes, zero invented classes, and no duplicate membership**. All 18 module IDs are nonempty, module class counts sum to 594, all 45 isolated vertices remain assigned, and all 31 annotation declarations remain assigned. The CSV header is exactly `class,cluster`. These checks validate partition completeness, not architectural correctness. [C] [A]

- **[C]** [classes.csv](inputs/classes.csv): exact inventory, package declarations, declaration kinds, and canonical outer types.
- **[D]** [dependencies.csv](inputs/dependencies.csv): directed binary internal type/member-use relationships; class-specific observations above are exact source/target rows.
- **[P]** [package_counts.json](inputs/package_counts.json): supplied per-package inventory counts.
- **[PD]** [package_dependencies.csv](inputs/package_dependencies.csv): supplied package-pair edge counts, checked against [D].
- **[DOC]** [package_documentation.txt](inputs/package_documentation.txt): matching-source package summaries. Labels such as `[DOC: collect]` identify the relevant package section. No linked external page was consulted.
- **[A]** [assignment.csv](assignment.csv): this proposal's final one-class/one-module assignment and derived module counts.
- [initial_hypothesis.md](initial_hypothesis.md): names-only checkpoint saved before dependency/documentation inspection.
- [architecture.json](architecture.json): structured rationale, observations, changes, limitations, and coverage results.
- [activity.json](activity.json): exact read scope, runtime identity available to the reviewer, method, and non-consultation record.
