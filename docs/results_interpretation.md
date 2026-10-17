# Revised Guava results: measurements and interpretation

## Main conclusion

The instructor-based revision changes the substantive result. **UE removal followed by ACDC reclustering has lower MQ on the same retained graph in all 30 releases. K-means reclustering improves that measure in 29 of 30.** The result is algorithm- and model-dependent; the study does not force omnipresent filtering to look beneficial.

The primary class graph now comes solely from the instructor extractor. The revised cohort contains 30 distinct major/minor families, includes Guava-owned public-suffix code, calibrates k on one inertia pilot and adds directional MoJoFM agreement. The paper's pure UE detector and the lecture-supported loop-free MQ formula remain. The original configuration and summaries are in `results/baseline_v1`, with the complete original study at Git commit `d970305`.

Source: `results/same_graph_comparisons.csv`, `results/run_manifest.json`, `config/analysis.json` and `config/versions.json`.

## Structural scale and the class population

| Measurement | 10.0 | 33.7.2 |
|---|---:|---:|
| Owned canonical class/type nodes | 317 | 594 |
| Instructor-derived directed internal edges | 1,289 | 2,750 |
| Nonannotation types | 311 | 563 |
| Owned annotation types | 6 | 31 |
| Graph isolates | 15 | 45 |
| Annotation isolates, a subset of both preceding categories | 5 | 31 |
| Graph-owned source code lines | 48,821 | 96,546 |

Class nodes grow by **87.4%**, edges by **113.3%**. The possible number of directed class pairs grows quadratically, so increasing edge counts can accompany decreasing graph density. A type count includes classes, interfaces, enums and annotation declarations; it is not a count of user features. Source files, raw bytecode classes and merged graph nodes are different populations.

The latest source-ownership inventory counts 610 Java files and 96,622 nonblank, noncomment physical Java lines, including package descriptors. The graph-linked file count excludes descriptors and yields 96,546 code lines. Both measures exceed the assignment's 10,000-line requirement. The complete source JAR includes a module descriptor and totals 96,646 code lines.

Sources: `results/sizes.csv`, `data/provenance/source_inventory_33.7.2.json`, `data/graphs/33.7.2/provenance.json`.

## The annotation correction is explicit, but metadata nodes remain

The primary graph is the normalized output of the unmodified instructor JAR. The supplemental ASM pass supplies owner/member evidence and preserves a separate broad graph. It cannot add its annotation-application or declaring-owner edges to the instructor result.

On 33.7.2, under the same revised source scope:

| Edge comparison | Count |
|---|---:|
| Primary instructor edges | 2,750 |
| Supplemental broad edges | 3,982 |
| Shared edges | 2,750 |
| Instructor-only edges | 0 |
| Supplemental-only edges | 1,232 |
| Supplemental-only edges targeting annotations | 1,145 |
| Other supplemental-only edges | 87 |

The public-suffix implementation adds three canonical types and eight instructor edges relative to the earlier common-namespace-only instructor audit. It carries Guava Authors headers, so excluding it solely by namespace was inappropriate for the stated whole-artifact scope.

The latest 31 owned annotation types are all isolates in the primary graph, which contains zero edges targeting them. They still contribute to node, singleton and clustering-feature counts. The study does not hide this by constructing its inventory from edge endpoints. It also does not equate every annotation with irrelevant metadata: ordinary code references recognized by the instructor remain eligible, and stable-release classes marked `@Beta` remain owned types.

Source: `data/graphs/33.7.2/extractor_comparison.json`, `classes.csv`, `dependencies.csv`, `instructor_raw.csv`, `supplemental_only_edges.csv`; scope rationale in `docs/modeling_decisions.md`.

## Thirty families rather than repeated patch observations

The frozen catalog contains 70 eligible stable release points in 45 major/minor families. The rule selects family ranks `round(i*44/29)`, then chooses one stable representative per selected family. The first family uses the explicit oldest boundary 10.0; all other selected families use their highest eligible stable patch at the frozen cutoff. The last is 33.7.2.

This removes repeated 33.4 and 33.7 observations from the original sample. Selecting 32.1.3 once is not the same as using several patches from the 32.1 family. Some selected families are adjacent because 30 observations from 45 families cannot all have an omitted family between them. The rule is uniform by family rank, not calendar time. No graph identity or metric outcome determined inclusion.

The revised selected graph series has **no byte-identical adjacent class-and-edge pairs**. That is an observed consequence, not a selection requirement. Had an identical pair remained, it would be reported as structural stability.

Sources: `data/provenance/family_selection.json`, `config/versions.json`, `scripts/select_versions.py`, `results/change_points.json`.

## Quality at the last sampled release

A1 is ACDC/full, A2 ACDC/UE-filtered, A3 k-means/full and A4 k-means/UE-filtered.

| Condition | Nodes | Edges | Clusters | Cohesion | Coupling | MQ |
|---|---:|---:|---:|---:|---:|---:|
| A1 | 594 | 2750 | 135 | 0.257499570 | 0.002200767 | 0.255298803 |
| A2 | 572 | 1724 | 149 | 0.243078638 | 0.001383960 | 0.241694679 |
| A3 | 594 | 2750 | 43 | 0.185153984 | 0.006164924 | 0.178989060 |
| A4 | 572 | 1724 | 43 | 0.205205260 | 0.003123447 | 0.202081813 |

The MQ formula is the lecture's mean normalized cohesion minus mean normalized coupling. It uses `n_i(n_i-1)` for loop-free directed internal pairs and includes every unordered cluster pair, including pairs with zero cross edges. The lecture also permits `n_i^2`; values computed with that alternative cannot be compared numerically without controlling the graph and partition. We retain the form used by the lecture's worked example.

ACDC has higher raw MQ than k-means on all 30 full graphs and all 30 retained graphs. This is a statement about this metric and these outputs, not accuracy. At the latest release ACDC/full has 135 clusters, including 47 singletons; k-means/full has 43 clusters and no singleton. Forty-five primary-graph isolates contribute to the ACDC wrapper's singletons. Equal-weight macro averaging makes these details consequential.

Sources: `results/metrics.csv` and each `results/versions/VERSION/A*_quality/per_cluster.csv` / `per_pair.csv`; lecture PDF pages 15-17; `docs/course_traceability.md`.

## Filtering evaluated on the same retained graph

Comparing raw A1 and A2 MQ changes both the node/edge population and the partition. The supplementary fair comparison first projects A1 onto exactly the retained nodes, removes any empty projected clusters, and evaluates it on the same retained edges as A2. A3/A4 follows the same procedure. This evaluates existing partitions; it does not create another recovered architecture.

| Algorithm | Positive changes | Negative changes | Mean MQ change across 30 | Latest projected-full MQ | Latest filtered MQ | Latest change |
|---|---:|---:|---:|---:|---:|---:|
| ACDC | 0 | 30 | -0.023836891 | 0.246415886 | 0.241694679 | -0.004721208 |
| k-means | 29 | 1 | +0.020552842 | 0.163768687 | 0.202081813 | +0.038313126 |

The latest filter removes 22 nodes and 1,026 incident primary edges, leaving 572 nodes and 1,724 edges. The number of isolates increases from 45 to 58. ACDC's new partition has 149 clusters and 60 singletons; k-means retains its requested 43 clusters but its largest group grows from 85 to 119 nodes. A higher k-means MQ therefore does not imply every aspect of module shape improved.

The comparison holds the evaluated population fixed and measures how the prescribed recovery process changes grouping. It does not establish a universal causal benefit of filtering, eliminate optimization sensitivity, or validate a semantic architecture. In particular, the uniformly negative ACDC result is reported without changing UE thresholds to seek a more favorable outcome.

Source: `results/same_graph_comparisons.csv`, `results/versions/33.7.2/A1_projected_to_retained_metrics.json`, `A3_projected_to_retained_metrics.json`, and the four latest metric files.

## UE remains faithful to the requested paper

The method removes between **6 and 23 classes** per release; **31 distinct identities** are removed at least once. It remains standalone UE with thresholds 0.85 and 0.90, not UE intersected with the older SIG classifier. Adding SIG would change the detector and require a separate rationale.

The last release's 22 removals include useful Guava APIs. “Omnipresent for clustering preprocessing” does not mean badly implemented, unnecessary or safe to delete from the actual library. The real member-evidence case study distinguishes `Preconditions` (remove: equality 0.927628, cardinality 0.996795) from `Iterators` (retain: equality 0.498035, cardinality 0.98). Many callers alone are insufficient because `Iterables` has a relatively specialized dedication to `Iterators`.

The supplemental member graph has 659 unresolved events covering 494 distinct recorded references; 335 events cross merged class boundaries. The ratio to all 53,424 raw observed member-use events is about 1.23%. This is an evidence diagnostic, not a completeness or false-negative rate: its denominator includes external and intraclass uses. Unknown inherited library behavior is not invented as internal member use.

Sources: `results/versions/*/ue.json`, `results/performance/case_checks.json`, `docs/ue_case_study.md`, and the supplied UE paper equations 1-3.

## What the k pilot does and does not establish

The 25.1 pilot has 554 nodes. A declared 14-candidate inertia grid selects **k=40**, with normalized chord gap 0.188513. Its target average is 13.85 classes per cluster. The final rule `ceil(n_full*40/554)` yields 23-45 clusters across the sampled full graphs and reuses a version's value after removal.

The nearby k=30 and k=50 gaps are 0.185458 and 0.180934. This is a broad elbow. Selecting the maximum is reproducible, but it does not demonstrate that exactly 40 conceptual components exist. The calibration and its size extrapolation depend on the structural features and chosen candidate interval; MQ is not used to pick them.

The pilot's matched-k diagnostic gives additional evidence about granularity. At 110 clusters, k-means MQ rises to 0.242393 from 0.160308 at its selected 40 clusters. ACDC at 110 clusters has MQ 0.319277. The gap narrows but remains. Thus granularity explains part of the pilot gap; matching k does not match cluster-size distributions, memberships or semantic responsibilities. The diagnostic is reported separately and does not choose the final configuration.

Sources: `results/pilot/pilot.json`, `k_calibration.json`, `k_inertia_curve.csv`, `k_candidates/` and `docs/pilot_decision.md`.

## MoJoFM and ARI are agreement measures

MoJoFM normalizes the move/join distance relative to a specified target partition. Reversing the inputs may change the distance and normalization. The study therefore preserves both directions, distances, denominators, source/target cluster counts and the exact class-universe hash. The 178 classical comparison pairs cover full/filtered, algorithm and temporal comparisons.

| Latest comparison | Shared nodes | Forward MoJoFM | Reverse MoJoFM | ARI |
|---|---:|---:|---:|---:|
| A1 → A2 | 572 | 81.4079 | 80.9783 | 0.602499 |
| A3 → A4 | 572 | 62.7273 | 61.4545 | 0.429671 |
| A1 → A3 | 594 | 43.7063 | 41.1150 | 0.187568 |
| A2 → A4 | 572 | 45.0909 | 43.6823 | 0.141595 |

For A1→A2 and A3→A4, the full partition is projected to retained nodes first. For temporal comparisons, both partitions use the intersection of class identities. MoJoFM is valid as agreement even without a validated expert reference. The absence of ground truth prevents an architecture-accuracy claim; it does not forbid calculation. ARI supplies a supplementary symmetric comparison.

Sources: `results/partition_comparisons.csv`, each per-release `partition_comparisons.json`, `docs/mojofm.md`.

## Source-backed changes worth discussing

**13.0.1→15.0:** classes increase from 382 to 441 and edges from 1,639 to 2,079 (+26.85%). There are 73 added and 14 removed class identities. The additions include 33 collection types, nine escaping types and nine I/O types. New observed collection identities include `ImmutableRangeMap` and `ImmutableRangeSet`. These are source-inventory observations, not a count of 73 new user features.

**19.0→21.0:** classes increase from 454 to 521 and edges from 2,113 to 2,509 (+18.74%). Of 76 added identities, 41 are under `com.google.common.graph`. The common-node edge Jaccard is 0.946362, indicating high persistence among surviving identities despite the additions. Because the interval contains an unsampled release, the graph comparison alone does not identify the first introduction commit.

**33.2.1→33.4.8:** classes decrease from 610 to 598, while primary edges change only from 2,840 to 2,826 (-0.49%). Fifteen internal `ElementTypesAreNonnullByDefault` annotation types disappear and four annotations are added. The exact source evidence shows the earlier declaration/use and the later package `@NullMarked` / external JSpecify import. With annotation applications excluded from primary edges, the migration affects type and isolate counts without creating the old large edge-count fall. It is still not proof of improved architecture.

**33.4.8→33.5.0:** classes decrease from 598 to 590 and edges from 2,826 to 2,744 (-2.90%), the largest relative primary-edge decline in the selected sequence. All eight removed identities belong to collections: seven nonannotation types and `GwtTransient`. The names include GWT serialization support, `ForwardingImmutableCollection` and `ImmutableEntry`. There are 87 removed and five added edges. The observations describe implementation support changes; a claim of removed public functionality requires separate API evidence.

All 29 transitions preserve exact added/removed class and edge lists, package breakdowns, annotation counts and common-node Jaccard. Source entry paths and hashes connect selected examples to the original artifacts. Source: `results/change_points.json` and the exact matching source JARs.

## AI experiment and evidence limits

The revised AI architecture recovery receives the latest **594-class, 2,750-edge** graph, class/package information and matching source documentation. The fresh session does not see old or new ACDC/k-means partitions, UE decisions or their scores. Its actual initial hypothesis, prompts, activity record, final assignment and module responsibilities are preserved under `results/ai`.

The coordinator evaluates that fixed partition on the full graph and projects the same assignment to the retained graph. These are two evaluations of one AI architecture, not two separate generated architectures. The AI also receives semantic names and documentation that structural algorithms do not receive; a comparison cannot be interpreted as a controlled superiority test with identical information. `docs/ai_reflection.md` gives the actual module findings and numerical results.

The fresh response has **18 modules covering all 594 classes exactly once**, including all isolates and annotation declarations. Its full-graph MQ is **0.094303**, and its retained-graph MQ is **0.089526**. The responsibilities include four collection groups, three concurrency groups, combined escaping across packages and network values with the owned public-suffix implementation. These are conceptual interpretations for review. AI → A1 MoJoFM is **28.57**, while A1 → AI is **61.63**; the directional difference reflects move/join asymmetry and normalization under substantially different granularities, not an accuracy advantage. [Evidence: `results/ai/evaluation.json`, `architecture.json`, `comparisons.csv`; `docs/mojofm.md`.]

## Course connections and limits

The recovered groups are an implementation view. The architecture-evolution lecture distinguishes intended, described and implemented architecture and different static/dynamic views. An erosion claim requires an intended constraint and evidence of a violation; MQ alone supplies neither.

The measured history is compatible with continuing change and structural growth, but does not verify all Lehman laws. Functional growth, user-perceived quality, invariant effort and organizational stability require data not measured here. The sparse family sample also has irregular time intervals. Counts are not rates unless the date denominator is used.

The requirements lectures motivate explicit operational definitions and traceability. Each reported metric can be traced through its partition and graph to source/version identities and artifact hashes. That traceability improves auditability but does not prove complete static analysis or semantic correctness. The strongest defensible claims are the recorded measurements under the declared scope, algorithms and assumptions.

## Verification boundaries

The revised implementation passes **60 focused tests**, including real compiled Java normalization/member fixtures, exact UE boundary cases, clustering/metric examples, elbow-selection rules and MoJoFM checks. The independent artifact audit recomputes saved scores and checks input/output consistency without recovering another architecture. The latest `results/validation.json` is authoritative for its pass count and status.

Synthetic UE timing for 10,000 classes and 200,000 references has a median **1.235303 seconds** across three detector-only repeats in the recorded environment. Input construction and extraction are outside that timing; process high-water RSS is not a per-call allocation measurement. No measured speedup against the old JNode tool is claimed.

A reproducible implementation can still encode a debatable modeling choice. Source scope, instructor coverage, annotation inventory, isolates, feature geometry, the broad pilot elbow and macro metric weighting remain explicit limits of the revised study. The original and revised aggregate differences combine multiple changes and are not a single-factor causal experiment.
