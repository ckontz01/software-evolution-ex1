# Initial names-only architecture hypothesis

Recorded before reading dependencies.csv, package_dependencies.csv, or package_documentation.txt. At this stage the only evidence inspected is classes.csv and package_counts.json; the experiment prompt supplies the release identity and graph-scope description. This is a qualitative hypothesis, not a finalized partition.

## Provisional responsibility areas

The inventory suggests the following starting areas, without fixing their number or assigning every class:

- **Core values and programming contracts:** optional values, preconditions, equivalence, functional adapters, object utilities, timing, reference lifecycle support, and shared API/platform annotations. The base package contains several distinct concerns; names alone do not establish which should become separate modules.
- **Collections and collection algorithms:** immutable and mutable containers, collection views, forwarding adapters, iteration, ordering, ranges, multimaps, multisets, and tables. This is the largest package (215 of 594 outer types). Range operations, specialized containers, and ordering look like candidate subareas, but splitting them requires evidence about their implementation relationships.
- **Caching:** cache construction, loading, eviction/removal, statistics, and local cache machinery.
- **Asynchronous execution and coordination:** futures, executors, services, synchronization, atomics, and rate/time limiting. The 83 names suggest that service lifecycle or synchronization could be separated if the evidence supports useful boundaries.
- **Graph models and traversal:** graph/network/value-graph interfaces, builders, mutable/immutable representations, connections, and traversal.
- **Hashing and probabilistic membership:** hash functions, sinks/funnels, hash codes, hashing streams, and Bloom filters.
- **Streams, files, and binary/text I/O:** sources, sinks, processors, readers, resource closing, file operations, and base encoding.
- **Primitive values and numerical methods:** primitive adapters, unsigned values, immutable primitive arrays, arithmetic, rounding, and statistics. Primitives and mathematics may be distinct responsibilities despite their common numeric vocabulary.
- **Network identifiers and protocol values:** addresses, host/port parsing, domains, media types, HTTP constants, and Guava-owned public-suffix support. Public-suffix names suggest an implementation relationship to InternetDomainName, which is only a hypothesis at this stage.
- **Text escaping:** escape abstractions and HTML/XML/URL escaping policies. PercentEscaper and UrlEscapers are in net but their names suggest a cross-package escaping responsibility; base text helpers may warrant a separate or adjacent concern.
- **Reflection and generic types:** type tokens, type resolution, invocation, class-path inspection, and type-to-instance maps.
- **Event dispatch:** event buses, subscription handling, dispatchers, and subscriber exceptions.

## Cautions and questions for the evidence phase

All 594 supplied canonical outer types, including annotations and isolated types, must remain in the final partition. The 18 package names offer useful vocabulary but are not ground truth for architectural boundaries. Familiar names such as Platform, Internal, and NullnessCasts are especially weak evidence: repeated names do not establish a shared responsibility across packages. Local support types will provisionally follow the implementation they support; this must be checked against the available relationships.

The next phase will check whether collections deserve a practical responsibility split, whether futures and service lifecycle warrant separate ownership, whether primitive adaptation should be distinct from mathematics, and whether the cross-package escaping and public-suffix hypotheses have concrete support. No module count, numeric quality target, or claimed intended design has been selected.
