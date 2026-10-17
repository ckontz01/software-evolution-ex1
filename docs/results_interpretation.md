# Interpretation of the completed Guava study

The completed study contains **30 selected stable releases and 120 final
architectures**: A1 (ACDC/full), A2 (ACDC/UE-filtered), A3 (KMeans/full) and
A4 (KMeans/UE-filtered). The independent artifact audit in
`results/validation.json` passes with no failures. This document explains the
observed results and their limits; it does not turn a structural score into a
claim about the intended architecture or users' experience.

The authoritative numerical tables are `results/sizes.csv`, `results/metrics.csv`,
`results/same_graph_comparisons.csv`, `results/evolution.csv` and
`results/runtimes.csv`. Each release directory also contains the complete class
partitions, per-class UE decisions, every cluster and cluster-pair metric term,
and execution metadata. Values below are rounded for reading.

## 1. Population, size and the meaning of the curves

The sample runs from **10.0, released 28 September 2011, to 33.7.2, released
29 September 2026**. Thirty observations were selected from the documented
eligible release sequence before inspecting clustering outcomes. At least one
stable release is skipped between every pair of observations. The sample covers
26 major/minor families. It is spaced by eligible release index, so observations
are not equally spaced in calendar time. These are repeated observations of one
software system, not 30 independent projects.

Only Guava-owned `com.google.common` production classes present in the selected
JRE artifact and its matching sources are nodes. Guava is itself a library, but
it is the subject under study: the excluded libraries are its external
dependencies and explicitly excluded bundled third-party code. Every release
uses the same boundary. Nested, local and anonymous classes contribute to their
outermost owner. Annotations, interfaces and enums are retained when they are
owned project types. An internal annotation named `Beta` is different from a
beta release; the latter is excluded by the version policy.

| Indicator | 10.0 | 33.7.2 | Net change |
|---|---:|---:|---:|
| Canonical classes | 317 | 591 | +274; +86.4% |
| Directed binary internal dependencies | 1,693 | 3,969 | +2,276; +134.4% |
| Code lines in the owned source-file population | 48,821 | 95,800 | +46,979; +96.2% |
| Directed graph density | 0.016901 | 0.011383 | Decreased |

The largest class count is 608 in 33.3.1; the largest dependency count is 4,518
in 33.2.0. Growth is therefore not strictly monotonic. Increasing edge counts
and decreasing density are compatible: the number of possible directed pairs
grows as n(n-1). These indicators describe the extracted graph's size and
connectivity, rather than one universal measure of software complexity.

The latest artifact contains 1,944 accepted binary classes, which become 591
canonical nodes after merging. The 1,353 additional nested/anonymous binary
classes are accounted for in `data/graphs/33.7.2/class_aliases.csv`; they have not
been ignored. Four further base binary classes are explicitly excluded by the
ownership policy. Three canonical nodes are graph isolates and appear in every
appropriate partition. The latest source population contains 180,244 physical
Java lines; the smaller code-line count excludes blank/comment-only lines.

Source: the selected manifest, extraction provenance, class aliases and source
size tables under `config/versions.json` and `data/graphs/<version>/`.

The two annotation transitions and the unchanged graph pairs below are
independently reproducible with `python scripts/audit_change_points.py`.
`results/change_points.json` preserves every added/removed edge with its input
CSV row, all class changes, production class/edge hashes, and the exact source
JAR entry hashes and line markers supporting the annotation-migration example.

### A visible rise largely reflects annotation changes

Between 30.1.1 and 31.1, classes increase from 568 to 600 and dependencies from
3,620 to 4,354. There are 35 added and three removed canonical types, with 792
added and 58 removed graph edges. **Thirty added types are annotations, and
748 of the 792 added edges target annotation types.** The number of typed
`TYPE_USAGE` edges rises from 2,485 to 3,190.

For example, 218 newly added graph edges target
`com.google.common.collect.ElementTypesAreNonnullByDefault`, and 97 target
`com.google.common.collect.ParametricNullness`. This is concrete evidence that
the observed jump includes a change in how nullness information is represented.
It does not establish that hundreds of new functional relationships appeared.

The UE detector correctly keeps these annotation types under its specified
member-use definition. In 31.1, the first annotation has 218 class-graph callers
but zero distinct caller classes in the member-use evidence. It has no
outside-class method/field use from which UE can infer omnipresence. A graph hub
and a UE omnipresent class are therefore different concepts.

### A later fall largely reflects moving nullness annotations outside the boundary

Between 33.3.1 and 33.4.1, the class count falls from 608 to 596 and edges from
4,513 to 3,930. Fifteen internal `ElementTypesAreNonnullByDefault` annotation
types disappear while three other annotation types are added. There are 587
removed and four added edges. **Of the 587 removed edges, 566 target the fifteen
removed internal annotation types.** Typed `TYPE_USAGE` edges fall from 3,343
to 2,762.

The pinned source archives support the interpretation directly. In 33.3.1,
`com/google/common/collect/Lists.java` uses
`@ElementTypesAreNonnullByDefault`, and its same-package annotation source exists.
In 33.4.1 that annotation source is absent; the matching
`com/google/common/collect/package-info.java` uses `@NullMarked` and imports
`org.jspecify.annotations.NullMarked`. JSpecify is external to the study scope,
and package metadata is excluded from the class-node population. The consistent
boundary consequently exposes a large decrease in recorded internal annotation
edges. This is not evidence, by itself, of a corresponding reduction in the
program's functional coupling or proof of successful architectural repair.

The class and dependency graphs for 33.4.1 and 33.4.3 are identical even though
their measured source code-line counts differ. The same is true of the graphs
for 33.7.0 and 33.7.2. Release identity, source text and this structural
abstraction can change independently.

## 2. The pilot and the final configuration

Release 28.2 was chosen by the middle sample index before evaluating results.
It has 555 canonical classes and 3,550 dependency edges. The pilot compared
ACDC SubGraph size settings 10, 20 and 40 and fitted KMeans once using the
predeclared k rule. No KMeans k sweep was performed.

The first adapter check exposed a real compatibility issue. Original ACDC's
`Node.getBaseName()` treats the final dotted component as a file extension.
Without an encoding, Java class IDs such as `p.A` and `p.B` can both produce
the container name `p.ss`. That invalidates an interpretation of their combined
output as one structurally discovered cluster. The rejected initial adapter
produced only 14 apparent clusters, including one containing 222 classes.

The repaired adapter appends `.java` to class identifiers only while calling
the unmodified original ACDC. The resulting basenames retain the complete class
identity, and memberships are decoded before measurement. Every run has a
`node_id_map.csv`, and an actual Java regression verifies that two disconnected
cliques in the same package remain distinct. The rejected adapter results are
not part of the 120 final architectures.

| Corrected pilot | Clusters | Largest cluster | Singleton clusters | Cohesion | Coupling | MQ |
|---|---:|---:|---:|---:|---:|---:|
| ACDC, size 10 | 90 | 44 | 3 | 0.384626 | 0.006082 | 0.378544 |
| ACDC, size 20 | 90 | 44 | 3 | 0.384626 | 0.006082 | 0.378544 |
| ACDC, size 40 | 90 | 44 | 3 | 0.384626 | 0.006082 | 0.378544 |
| KMeans, k=17 | 17 | 60 | 0 | 0.088695 | 0.011811 | 0.076884 |

The three corrected ACDC partitions are byte-identical. Thus the pilot supplies
no evidence for preferring 10 or 40 over the documented default 20. We retain
`+so`, size 20 and fine flat output for every final release. This is a sensitivity
observation on one predetermined release, not a claim that size never matters
for any graph. The size setting applies to a stage of SubGraph recovery;
subsequent adoption can enlarge clusters. It is not a strict final size cap.

KMeans uses the same 712-class union schema throughout, with 1,424 outgoing and
incoming feature coordinates. Identity entries exist only in features, and each
row is L2-normalized. k is ceil(sqrt(n_full/2)); the full-release value is reused
for its filtered condition. Actual final k ranges from 13 to 18. All final fits
reach the requested number of clusters. The heuristic is a transparent
granularity choice and is not presented as an optimal-k theorem from the lectures.

Source: `results/pilot/pilot.json`, `config/analysis.json`, the corresponding
adapter/test sources and each final run's metadata. Metric equations are from
Architecture Reconstruction PDF pp. 15–17; see `docs/course_traceability.md`.

## 3. Recovery quality across the 30 observations

These are unweighted means across the selected releases; dense periods in the
release history are not converted into longer durations by averaging.

| Condition | Mean clusters | Mean cohesion | Mean coupling | Mean MQ | Mean size-weighted cohesion |
|---|---:|---:|---:|---:|---:|
| A1: ACDC/full | 84.37 | 0.392085 | 0.006557 | 0.385528 | 0.243011 |
| A2: ACDC/filtered | 84.20 | 0.391001 | 0.005212 | 0.385789 | 0.243417 |
| A3: KMeans/full | 16.80 | 0.104287 | 0.010071 | 0.094216 | 0.073967 |
| A4: KMeans/filtered | 16.80 | 0.122416 | 0.007840 | 0.114576 | 0.078456 |

ACDC has the higher lecture MQ in every corresponding release comparison, but
it also produces many more, generally smaller clusters. The lecture MQ averages
clusters equally and averages all unordered cluster pairs, including pairs with
zero edges. Cluster size, singleton treatment and the number of cluster pairs
therefore affect the interpretation. The result supports higher structural
density under this particular score and granularity; it does not establish
universal superiority or correctness against an intended architecture.

KMeans minimizes within-cluster squared Euclidean feature distance, rather than
optimizing the lecture MQ directly. Both algorithms were applied with one
documented representation/configuration. A different feature representation or
granularity could change their scores. No such unperformed alternative is
reported as a measured result.

### Does removing omnipresent classes help?

UE removes between 6 and 24 classes per release. On average, this is about
3.21% of the class population but removes 24.35% of the graph's edges. That is
consistent with targeting widely used types under the method's member-use
definition. It also means a direct full-versus-filtered score comparison changes
both the partition and the graph on which it is evaluated.

For the main filtering comparison, the full partition is first restricted to
the retained classes. Both that projected partition and the newly recovered
filtered partition are then evaluated on **the same induced retained graph**.

| Same-graph comparison | Positive MQ change | Negative change | Mean change | Median change |
|---|---:|---:|---:|---:|
| Projected A1 versus recovered A2 | 23/30 | 7/30 | +0.009776 | +0.009588 |
| Projected A3 versus recovered A4 | 26/30 | 4/30 | +0.022902 | +0.019967 |

The evidence supports a frequent improvement in this score, especially for the
chosen KMeans representation, with explicit counterexamples. It does not support
the statement that removing UE classes always improves architectural quality.
For contrast, directly comparing A2 with A1 on their different graph populations
would show positive differences in only 13 of 30 releases. The interpretation
changes substantially when the population is held constant.

The latest release illustrates both outcomes. UE removes 22 of 591 classes,
leaving 569 classes and 2,886 of 3,969 edges. The change removes 3.72% of nodes
and 27.29% of edges.

| Latest condition | Clusters | Largest cluster | Cohesion | Coupling | MQ |
|---|---:|---:|---:|---:|---:|
| A1 | 95 | 69 | 0.407818 | 0.004596 | 0.403222 |
| A2 | 98 | 97 | 0.391992 | 0.003950 | 0.388041 |
| A3 | 18 | 96 | 0.110793 | 0.010189 | 0.100604 |
| A4 | 18 | 93 | 0.127155 | 0.007951 | 0.119204 |

On the latest retained graph, projected A1 has MQ 0.391237 and recovered A2
has 0.388041: **the same-graph change is -0.003196**. Projected A3 has 0.096592
and recovered A4 has 0.119204: **the same-graph change is +0.022611**. These are
more defensible statements than attributing every raw MQ difference to removal
alone. The removal changes the analysis population, not Guava's actual source
or behavior.

For a precise oral example of why a class is removed or kept, use
`docs/ue_case_study.md`: `Preconditions` is removed, while `Iterators` is kept
despite many callers. The independent exact-fraction audit records all caller
dedications and the underlying member-reference CSV rows.

## 4. Stability and what it measures

Temporal comparisons use common canonical class identities. The edge Jaccard
index is computed only between edges whose endpoints both survive in the two
observations. Its mean is 0.972432. Mean adjusted Rand agreement of the recovered
partitions on the common classes is 0.743497 for ACDC and 0.524593 for KMeans.
These are descriptive stability indicators, not measures against a gold standard.

At 30.1.1 to 31.1, common-node edge Jaccard is 0.980457, while ACDC agreement
is 0.713035 and KMeans agreement is 0.272115. The latter is the lowest KMeans
agreement in the sample. Newly added annotation targets alter feature rows even
when relations between old classes remain similar, and the size heuristic also
changes k from 17 to 18 at this transition. Both are relevant changes; the
observations do not isolate one as the sole cause.

At 33.3.1 to 33.4.1, common-node edge Jaccard is 0.997459, despite the conspicuous
fall in total edges. Many lost edges touch removed annotation nodes and therefore
do not enter that common-node comparison. ACDC agreement is 0.795074 and KMeans
agreement 0.366536. This illustrates why a graph statistic, total counts and
partition stability answer different questions.

Both algorithms have temporal agreement exactly 1 for the identical-graph
transitions 33.4.1 to 33.4.3 and 33.7.0 to 33.7.2. Fixed seeds/configurations
support reproducibility on the same data. They do not guarantee that a small
input change leaves a fitted partition unchanged.

Source: `results/evolution.csv`, complete graph diffs in the extracted CSVs and
per-version run metadata. Adjusted Rand and same-node Jaccard are explicitly
supplementary engineering measurements; they are not attributed to unverified
lecture slides.

## 5. Performance and independent verification

The recorded stage totals for all 30 releases are 14.14 seconds for extraction,
1.79 seconds for UE including member-CSV reading, 13.50/9.78 seconds for A1/A2,
and 1.69/1.47 seconds for A3/A4. These timings describe this environment and
these inputs. They exclude downloads, tool provisioning, report generation and
some result-serialization work, so their sum is not a claimed end-to-end runtime.

The separate synthetic detector benchmark uses 20,000, 100,000 and 200,000
distinct member references, with medians 0.0875, 0.5671 and 1.2360 seconds. Input
construction and extraction are outside that timer; validation, aggregation,
diagnostics and deterministic output ordering are included. The detector uses
hashed distinct-reference aggregation and no shortest-path enumeration. The
benchmark supplies measured scaling evidence, while the implementation explains
why it avoids an expensive all-pairs path approach. Source:
`results/performance/ue_benchmark.json` and `docs/omnipresent.md`.

`scripts/validate_results.py` uses the standard library and imports no production
metric, detector, clustering or extraction function. It recomputes lecture MQ
from individual edge contributions, UE decisions with exact rational arithmetic,
and adjusted Rand values from contingency tables. It checks every final
partition's population, every cluster/pair table, the 90 pinned artifact hashes,
binary/source ownership and outer-class aliases, internal graph boundaries,
feature-coordinate identities, k policy, frozen implementation/configuration
hashes, aggregate row inventories and identical retained-graph populations.
The persisted result reports **3,362,762 checks and zero failures** for this run.

Those checks establish consistency and reproducibility of the recorded structural
experiment. They cannot establish that bytecode captures reflection, every
possible runtime dispatch, design intent, feature usefulness or user-perceived
quality. The bounded member resolver's actual limitations are recorded alongside
extraction evidence rather than hidden by a complete-partition claim.

## 6. Connections to the course and claims to avoid

The architecture lectures distinguish intended, described and implemented
architecture. This study reconstructs a static structural view of the implemented
system. Drift or erosion requires a comparison with intended architectural
constraints; a lower MQ alone does not demonstrate either. A shared utility, a
hub smell and a paper-defined omnipresent module likewise need not be the same
set of classes. See `docs/course_traceability.md` for verified source references.

The longer-term growth is consistent with the continuing-change and continuing-
growth themes discussed with Lehman's laws. However, class/line growth is not a
measurement of new functionality, and this one retrospectively sampled library
cannot validate all eight laws. The annotation transitions are a practical
counterexample to reading every jump as functional growth or declining quality.

Requirements lectures motivate explicit definitions and traceability. Here the
chain is: requirement and sampling rule → immutable artifacts → ownership and
merge decisions → dependency/member evidence → detector decisions → partitions
→ exact metric terms → qualified interpretation. Automated evaluation makes
errors and comparisons reviewable; it does not remove the need to check whether
the chosen measures answer the intended question.

An oral defense should therefore be able to explain a single input edge, the
canonical owner of an anonymous-class member, one exact UE decision, one
hand-calculated MQ, the ACDC suffix repair, the fixed KMeans rule, and a concrete
release transition. Those examples explain the full pipeline more convincingly
than memorizing only the four latest scores.
