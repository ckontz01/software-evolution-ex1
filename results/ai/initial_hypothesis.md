# Initial architecture hypothesis — names and package counts only

## Evidence available at this checkpoint

I have read `results/ai/prompt.txt`, `results/ai/inputs/classes.csv`, and `results/ai/inputs/package_counts.json` only. I have not yet read dependencies, package dependencies, or package documentation. The manifest contains 591 canonical outer classes in 17 packages. The `collect` package has 215 classes, `util.concurrent` 83, `graph` 53, and `base` 51 plus one `base.internal` class.

## Qualitative hypothesis

Guava appears to be a collection of reusable library capabilities with a shared foundation, rather than one application organized around a single business workflow. My provisional responsibility map is:

- **Foundational contracts and runtime support:** preconditions, optional values, functions/predicates/suppliers, equivalence, exceptions, reference cleanup, and compatibility annotations.
- **Text processing and escaping:** matching, splitting/joining, character conversion, escape mechanisms, and HTML/XML specializations. Names suggest considering base text helpers and URL escaping here, but their ownership is unresolved.
- **Collections:** collection implementations, views, iteration, ordering, immutable variants, multimaps/multisets, tables, and ranges. The 215-class package probably deserves a more detailed conceptual map, but names alone do not justify a particular split.
- **Primitive and mathematical utilities:** primitive wrappers/arrays and numeric algorithms/statistics; whether these form one responsibility or two remains open.
- **Caching:** cache loading, eviction/removal policies, and local cache implementation support.
- **Concurrency and execution:** futures, executors, services, locks, atomics, and time/rate controls. The service lifecycle and synchronization families may warrant their own boundaries after dependency inspection.
- **Graph models and traversal:** graphs, value graphs, networks, builders, connection representations, and traversal.
- **Hashing and probabilistic structures:** hash functions, hashers, funnels, and Bloom filters.
- **I/O and encodings:** byte/character sources and sinks, streams, files/resources, and base encodings.
- **Network value handling:** addresses, hosts/domains, media types, and protocol names, with escaping ownership still open.
- **Reflection and type information:** generic type modeling, invocation, classpath inspection, and type-indexed values.
- **Event dispatch:** registration, subscribers, delivery, and subscriber exceptions.

## Decisions deliberately deferred

This is a qualitative hypothesis, not a second class partition. I have not fixed a module count or allocated every class. I will test whether collection families and concurrency responsibilities have credible boundaries, whether text helpers can be separated from the base foundation, and whether small escaping packages should be combined. Package names are a strong initial cue and may bias this map. Shared helpers and isolated annotations still require one explicit final owner; low degree will not be grounds for omission. Dependency counts will be descriptive evidence, not an optimization target or an architecture-quality score.
