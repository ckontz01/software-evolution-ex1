# Reflection on the revised AI recovery

## What was actually done

A fresh GPT-6 Astra Pro session recovered one conceptual responsibility partition of **Guava 33.7.2 JRE from the revised 594-class, 2,750-edge instructor-derived graph**. It received five fixed evidence files: the complete class inventory, directed internal dependencies, package counts, aggregate package dependencies, and unmodified package documentation from the matching source JAR. The exact task and launch instruction are preserved in `results/ai/prompt.txt` and `launch_message.txt`. The new `activity.json` records read order and the initial checkpoint; `experiment.json` records all supplied input hashes. This is a newly recorded experiment, with a different assignment and response from the original study. [Evidence: `results/ai/experiment.json`, `activity.json`, `evaluation.json`; original record at Git commit `d970305`.]

The session first read class names, declaration kinds and package counts, then saved `initial_hypothesis.md` before reading dependencies or documentation. That checkpoint proposes qualitative responsibility areas without final class membership or a fixed module count. The session then produced **one final partition of 18 modules**, assigning all 594 classes exactly once, including all 45 isolates and all 31 annotation declarations. There are no invented or external classes. The coordinator calculated quality and agreement only after the fresh session completed. The retained-graph scores project this same partition; they are not a second AI recovery. [Evidence: `activity.json`, `assignment.csv`, `evaluation.json`.]

The launch prohibited reading baseline partitions, UE decisions, quality results, earlier experiment output, project history, class implementation files or external sources. The activity record reports that these restrictions were followed. Input/output hashes and assignment checks establish what was supplied and saved; they cannot independently prove every internal process declaration or erase pretrained knowledge. The runtime exposed the model name but no precise underlying API snapshot, sampling seed or temperature controls. A repeatable evidence packet therefore does not promise a bit-identical fresh model response. [Evidence: `experiment.json`, `activity.json`; `results/validation.json` limitations.]

## What the additional evidence changed

The names-only checkpoint left several boundaries unresolved. The final response divides collections into four responsibilities: core collections/ordering, multimaps/multisets, tables, and ranges. Documentation distinguishes their contracts, while the graph exposes shared helpers and implementation links. This is a useful conceptual split but not evidence that the four groups could immediately become independent compilation units. [Evidence: `initial_hypothesis.md`, `architecture.json` changes 1 and module boundary rationales.]

Concurrency becomes futures/execution, service lifecycle, and synchronization/limits. The two forwarding blocking-container adapters from `util.concurrent` are assigned to collection machinery because their direct implementation links use collection forwarding types. `Monitor` remains a synchronization concept despite the graph showing only two incoming lifecycle consumers. This illustrates a semantic ownership judgment that a purely structural method need not reproduce. [Evidence: `response.md`, sections on collection and concurrency responsibilities; `assignment.csv`.]

Primitive value/storage helpers and arithmetic/statistics are separated. Basic string helpers remain with foundational contracts; escaping is combined across generic, HTML, XML and URL packages. All three Guava-owned public-suffix types join domain/network values, supported by `InternetDomainName` dependencies. These refinements follow the supplied evidence, but one staged session cannot establish that extra documentation improves architectural accuracy. There is no randomized prompt comparison, maintainer ground truth or search among finalized AI responses for a favorable score. [Evidence: `architecture.json` changes 3–6.]

## Complete final module inventory

| Module | Classes | Responsibility |
|---|---:|---|
| Core values and programming contracts | 57 | Basic values, argument checks, functional adapters, text helpers, timing, reference lifecycle support, and shared API/platform annotation declarations. |
| Core collections and ordering | 127 | Ordinary maps, bimaps, lists, sets and queues; immutable implementations of those types; collection views, iteration, ordering, forwarding decorators, interning, and shared collection support. |
| Multimaps and multisets | 59 | Multiple-value mappings and occurrence-counting collections, including their interfaces, mutable and immutable implementations, filtering views, sorted variants, and dedicated forwarding adapters. |
| Two-dimensional tables | 16 | Row/column-keyed Table APIs, mutable and immutable representations, forwarding views, and table-specific collectors. |
| Ranges and interval collections | 15 | Range endpoints and bounds, discrete domains, contiguous sets, and range-set/range-map representations. |
| Caching and removal policy | 22 | Cache APIs, loading, construction and configuration, eviction/removal policy, statistics, and local cache implementation support. |
| Futures and execution runtime | 58 | Future values and composition, listening executors, task submission and sequencing, executor adapters, thread factories, execution exceptions, interrupt/wait helpers, and shared runtime support. |
| Service lifecycle management | 8 | Service state/lifecycle APIs, service implementation templates, service groups, and lifecycle listener dispatch. |
| Synchronization and execution limits | 15 | Atomic state utilities, locks and monitors, striped/cycle-detecting synchronization, rate limiting, and time limits. |
| Graph models and traversal | 53 | Graph, network and value-graph APIs, builders, mutable/immutable representations, adjacency/connection machinery, and traversal. |
| Hash functions and probabilistic membership | 33 | Hash functions and codes, hashers, primitive sinks/funnels, digest and checksum adapters, hashing streams, and Bloom filters. |
| Streams, files and resource I/O | 37 | Byte/character sources and sinks, streams and readers, file/resource operations, resource closing, line processing, and base encoding. |
| Primitive value utilities | 25 | Primitive-type utilities and conversions, unsigned value types, immutable primitive arrays, and associated platform helpers. |
| Arithmetic and statistics | 16 | Arithmetic and rounding over numeric values, quantiles, statistical summaries/accumulators, and linear transformations. |
| Network identifiers and protocol values | 10 | IP addresses, host/port specifications, domain names and owned public-suffix support, media types, and HTTP constants. |
| Text escaping policies | 16 | Generic character/Unicode escape abstractions, escaper builders, and HTML, XML, and URL escaping policies. |
| Reflection and generic types | 16 | Generic type capture/resolution, type tokens, invocation and parameter inspection, type-to-instance maps, class-path inspection, and reflection helpers. |
| Event subscription and dispatch | 11 | Event bus APIs, synchronous/asynchronous dispatch support, subscription declarations, subscriber discovery, and exception handling. |

These are the module names and responsibilities returned by the fresh session. `assignment.csv` is authoritative for exact membership; a broad prose label does not add or duplicate a class. Package-local helpers and isolated annotations receive one stated owner even where multiple conceptual homes would be defensible. [Evidence: `architecture.json`, `assignment.csv`.]

## Numerical comparison on matching graphs

| Baseline | Graph | Baseline MQ | AI MQ | MoJoFM AI → baseline | MoJoFM baseline → AI | ARI |
|---|---|---:|---:|---:|---:|---:|
| A1 | full | 0.255299 | 0.094303 | 28.57 | 61.63 | 0.166571 |
| A2 | retained | 0.241695 | 0.089526 | 32.85 | 63.18 | 0.200843 |
| A3 | full | 0.178989 | 0.094303 | 32.52 | 61.63 | 0.170132 |
| A4 | retained | 0.202082 | 0.089526 | 33.82 | 63.36 | 0.153464 |

On the full **594-node, 2,750-edge** graph, AI cohesion is **0.096598**, coupling **0.002295**, and lecture MQ **0.094303**. Projection onto the **572 retained nodes and 1,724 edges** gives cohesion **0.090686**, coupling **0.001159**, and MQ **0.089526**. Both have 18 nonempty modules. The largest full AI module has 127 classes; A1 has 135 clusters and A3 has 43, so granularity differs substantially. [Evidence: `results/ai/metrics.json`, `retained_metrics.json`, `comparisons.csv`; `results/metrics.csv`.]

MoJoFM is directional. Here **AI → A1 is 28.57**, while **A1 → AI is 61.63**. Transforming a coarse 18-module partition into a much finer partition often requires many class moves; in the reverse direction, joins can combine existing groups. The normalization also depends on the target partition. Reporting only the larger direction would hide a material part of the comparison. Neither direction is an accuracy score because neither partition is a validated intended architecture. ARI, which is symmetric, is retained as supplementary agreement evidence. [Evidence: `results/ai/partition_comparisons.json`; `docs/mojofm.md`; Lecture 6–7 reconstruction material.]

The AI partition has lower lecture MQ than each baseline on the corresponding graph, but only **40.65%** of full-graph edges cross its module boundaries. A1's corresponding fraction is **63.93%**. These observations can coexist: the lecture MQ averages cluster densities and pairwise coupling, whereas the boundary-edge fraction counts edge mass. Large semantic modules often absorb more internal edges while having a lower internal density. Neither statistic alone proves a superior architecture. [Evidence: `results/ai/metrics.json`; `results/metrics.csv`; lecture MQ definitions in `docs/course_traceability.md`.]

## Benefits and limits of the result

The useful AI contribution is a navigable conceptual map with names, representative classes and explicit ownership reasoning. For example, the network module includes the owned suffix implementation, and the escaping module collects a responsibility that spans several packages. The response also highlights ambiguous cases such as `GeneralRange`, shared collection serialization/collectors and `Monitor`. These statements can guide a human review more directly than a numbered structural cluster. [Evidence: `response.md`, `architecture.json`.]

Package organization and documentation vocabulary strongly influence the result. Most small packages remain recognizable, while collection/concurrency subdivisions and cross-package escaping show that package equality was not enforced. That does not eliminate package bias. The model also has pretrained knowledge, and it received semantic names and documentation that ACDC and k-means did not use as features. This is an intentional difference in information, not a controlled test of algorithm superiority on identical inputs. [Evidence: `experiment.json`, `response.md` package-bias discussion; `config/analysis.json`.]

The 45 isolates are a specific confidence limit: their supplied dependency rows cannot determine ownership. All 31 annotation declarations are isolated under the instructor graph, so absence of annotation application edges cannot be read as absence of annotation semantics. Internal constant and utility classes can also have external clients that this scoped graph does not include. The response preserves these classes and states conventional ownership rather than treating isolation as proof of irrelevance. [Evidence: `activity.json` validation; `response.md` confidence limits; `data/graphs/33.7.2/classes.csv` and `dependencies.csv`.]

A static binary graph with inner/anonymous classes merged does not establish runtime interactions, reflection targets, resource coupling, separate deployment feasibility, future design intent or team ownership. Maintainers would need to assess whether these module boundaries match their change responsibilities, visibility constraints and compatibility commitments. The exact prompts and outputs make this proposal reviewable; they do not establish that the model discovered a unique correct design. [Evidence: `response.md` maintainer-validation section; Lecture 5 distinction between implemented and intended architecture.]

## Use on another project and oral-exam explanation

For longitudinal measurement, the structural pipeline is the more straightforward repeatable procedure: select releases before measuring outcomes, pin data, apply one explicit extractor model, execute fixed clustering policies and calculate documented metrics. A language model can complement it when given a bounded, verifiable evidence packet and required to produce complete membership and evidence-linked rationale. I would use disagreements to choose questions for maintainers, not let MQ or an AI label alone approve a refactoring or deletion.

In an oral examination: “We gave a fresh session the corrected latest graph and matching package documentation. It saved an initial names-only hypothesis, then made one final 18-module assignment for all 594 classes. We scored that fixed output afterward using the same lecture MQ and bidirectional MoJoFM as the baselines. Its full MQ was 0.094303; the output is useful as a semantic explanation, but different information, cluster sizes and missing ground truth prevent an accuracy claim.”

The complete original fresh response remains unedited in `results/ai/response.md`. This reflection summarizes and evaluates it; it does not rewrite its output to improve scores.
