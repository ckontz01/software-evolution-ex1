# Understanding the current Guava results

The current study covers 30 releases, with one final A1–A4 partition for each. The strongest comparison of Usage Equality filtering holds the retained graph fixed: **ACDC reclustering raises MQ in 0 releases and lowers it in 30; k-means raises it in 29 and lowers it in 1.** This is an observed result under the declared model, not an assumption that removing widely used classes must help. [Same-graph comparisons](../results/same_graph_comparisons.csv)

## What changed in this revision

The release sample now includes all 24 major versions from 10 through 33, the latest endpoint and five minor releases selected by a calendar-gap rule. The shortest gap is 74 days and the median is 141 days. The earlier family-rank sample placed four 23.x releases within 56 days; the current sample removes that concentration. Selection uses the captured release dates only. It does not inspect graphs or scores. [Selection record](project_selection.md)

Current agreement figures and tables use MoJoFM. The dependency extractor, ownership boundary, Usage Equality thresholds, isolate policy, feature construction and k-selection strategy remain unchanged. The new cohort changes the union of class coordinates and the middle release, so all final partitions are regenerated after a new pilot. The recorded AI proposal remains the same earlier response because its latest-release graph inputs are unchanged. [Model](modeling_decisions.md) · [AI reflection](ai_reflection.md)

The latest graph is identical to the preceding instructor-extractor study, but the rerun gives A4 a different k-means partition. The feature union still contains 715 class identities; it now includes `com.google.common.hash.Sink` in place of `com.google.common.base.Java8Usage`. The changed coordinates and their order may affect numerical ties during fitting, although that mechanism was not isolated experimentally. This difference should not be described as evolution within the unchanged latest release. The saved feature hashes and execution records identify the inputs of each run. [Current feature union](../data/graphs/feature_universe.json) · [Run record](../results/run_manifest.json)

## Classes and dependencies over time

The graph grows from **317 to 594 canonical owned types** and from **1,289 to 2,750 directed dependencies**. The respective increases are **87.4%** and **113.3%**. Inner, local and anonymous classes are merged into their enclosing type. Each ordered class pair counts as one edge, even if several occurrences or relationship categories connect it. [All 30 size rows](../results/sizes.csv)

The artifact boundary includes Guava's common packages and its owned public-suffix implementation. External libraries are excluded from both ends of every edge. The instructor's extractor supplies the primary edges; supplemental member references support Usage Equality separately. Class and edge growth describe the implementation visible to this process. They do not directly count user features or prove that the design has deteriorated.

The plotted observations are equally spaced along the release axis, but their dates are not. A longer interval offers more opportunity for change. Source-level additions, removals, renames, compiler output and extraction coverage can all influence the graph. Conclusions about evolution therefore need both the counts and the interval/source context. [Acquisition](data_acquisition.md)

## Annotation declarations and isolates

The latest inventory includes **31 owned annotation types** and **45 isolates**, with **31 annotation isolates**. Annotation applications do not add supplemental edges to the primary graph. The latest count of annotation-target edges is **0**. The declarations remain in the inventory because ownership and observed connectivity are separate questions. [Graph provenance](../data/graphs/33.7.2/provenance.json)

This choice affects clustering. ACDC's edge-list input cannot represent a node with no incident edges, so the adapter restores actual isolates as singletons. Their cohesion is zero under the stated MQ convention. K-means keeps an isolate's identity entry in its feature vector. Annotation declarations can therefore change counts and MQ without becoming dependency hubs. The course does not explicitly require isolates to be discarded; keeping the complete owned inventory is a disclosed modeling choice.

## Latest architecture quality

| Condition | Nodes | Clusters | Cohesion | Coupling | MQ |
| --- | --- | --- | --- | --- | --- |
| A1 | 594 | 135 | 0.257500 | 0.002201 | 0.255299 |
| A2 | 572 | 149 | 0.243079 | 0.001384 | 0.241695 |
| A3 | 594 | 43 | 0.185154 | 0.006165 | 0.178989 |
| A4 | 572 | 43 | 0.188325 | 0.003480 | 0.184844 |

ACDC has higher raw MQ than k-means in **30 of 30 full-graph comparisons** and **30 of 30 retained-graph comparisons**. These comparisons use the same graph within each pair. They do not establish accuracy against the intended architecture. [Complete quality measurements](../results/metrics.csv)

MQ is mean cluster cohesion minus mean coupling over cluster pairs. The chosen directed-graph cohesion denominator is `n(n-1)`, matching the lecture's worked example. Every cluster has equal weight in the cohesion average, and zero-edge pairs remain in the coupling average. A partition containing many small groups can therefore score differently from one containing fewer large groups even when both tell a useful story. The latest full-graph cluster counts are **135 for ACDC** and **43 for k-means**. The detailed files also report singletons, largest groups, weighted cohesion and crossing-edge fractions. [Metric definitions](course_traceability.md)

## What filtering changes on the same retained graph

Usage Equality removes **22 of 594 classes** from the latest graph, leaving **572 classes and 1,724 edges**. A direct comparison of full and filtered MQ changes both the grouping and the population. To isolate regrouping, the full partition is first projected onto those same retained nodes and edges. It is then compared with the newly clustered filtered graph.

| Method | Higher MQ | Lower MQ | Mean change | Latest change |
| --- | --- | --- | --- | --- |
| ACDC | 0 | 30 | -0.023655 | -0.004721 |
| k-means | 29 | 1 | +0.021299 | +0.021075 |

A positive change favors reclustering under this metric; a negative value favors keeping the original grouping of the remaining classes. Neither outcome implies that a useful utility should be deleted from Guava. The detector is a preprocessing step for recovering groups. Its fixed member-use thresholds are not adjusted to make filtering appear beneficial. [UE method](omnipresent.md) · [Worked class decisions](ue_case_study.md)

At the latest release, the largest k-means cluster contains **85 classes before filtering** and **118 afterwards**. A change in MQ therefore should be read alongside actual group sizes and membership, rather than treated as a complete assessment of every architectural property.

## Choosing k and interpreting its effect

The current pilot is **25.0**, with **554 classes**. The fixed 14-candidate inertia sweep selects **k=40** with normalized gap **0.189102**. The final rule `ceil(n_full*40/554)` transfers its approximate **13.85 classes per cluster** to the other releases. Each release reuses its full-graph k after filtering, unless fewer nodes remain. The actual full-graph cluster counts range from **23 to 45**. [Pilot record](pilot_decision.md)

Selecting the same seven relationship types does not itself determine k. The course asks how k was chosen; the single-release elbow and subsequent scaling are our declared strategy. The sampling revision retains that strategy and recomputes its inputs. Inertia measures distance fit in the feature space, not semantic correctness, and the candidate range affects the selected elbow. The matched-ACDC-k pilot comparison examines granularity separately without choosing k from MQ.

## MoJoFM agreement

| Comparison | Classes | Forward MoJoFM | Reverse MoJoFM |
| --- | --- | --- | --- |
| A1 → A2 | 572 | 81.4079 | 80.9783 |
| A3 → A4 | 572 | 60.4356 | 58.3636 |
| A1 → A3 | 594 | 43.7063 | 41.1150 |
| A2 → A4 | 572 | 47.1869 | 42.7798 |

MoJoFM counts the moves and joins needed to transform one partition into another and normalizes the distance against the target partition. Forward and reverse scores can differ. For filtering comparisons, both inputs use retained classes. Temporal comparisons use the intersection of class identities between adjacent sampled releases. Neither an algorithmic partition nor package structure is automatically a validated ground truth. The scores describe agreement. [All comparisons](../results/partition_comparisons.csv) · [MoJoFM implementation](mojofm.md)

The temporal figure shows edge overlap as Jaccard similarity multiplied by 100 and partition agreement as MoJoFM from the previous sample to the current sample. These answer different questions: whether recorded edges persisted and whether the recovered group memberships persisted. The saved files also contain the reverse temporal MoJoFM direction.

## Relating large graph changes to the source

The following intervals have the largest absolute percentage edge-count changes. They were chosen for explanation after sampling and measurement, not used to decide which releases to include.

| Interval | Classes before/after | Edges before/after | Edge change |
| --- | --- | --- | --- |
| 10.0 → 11.0 | 317 → 355 | 1289 → 1469 | +13.96% |
| 11.0 → 12.0 | 355 → 373 | 1469 → 1597 | +8.71% |
| 13.0.1 → 14.0 | 382 → 412 | 1639 → 1945 | +18.67% |
| 19.0 → 20.0 | 454 → 514 | 2113 → 2453 | +16.09% |


**10.0 to 11.0:** 46 class names appear and 8 disappear. The largest additions are com.google.common.hash (17), com.google.common.collect (7), com.google.common.math (6). The largest removals are com.google.common.collect (4), com.google.common.cache (2), com.google.common.util.concurrent (2). Edge Jaccard among shared classes is 0.9508.


**11.0 to 12.0:** 20 class names appear and 2 disappear. The largest additions are com.google.common.collect (8), com.google.common.reflect (7), com.google.common.base (2). The largest removals are com.google.common.collect (1), com.google.common.hash (1). Edge Jaccard among shared classes is 0.9290.


**13.0.1 to 14.0:** 37 class names appear and 7 disappear. The largest additions are com.google.common.collect (19), com.google.common.io (8), com.google.common.reflect (4). The largest removals are com.google.common.collect (5), com.google.common.base (2). Edge Jaccard among shared classes is 0.9029.


**19.0 to 20.0:** 65 class names appear and 5 disappear. The largest additions are com.google.common.graph (41), com.google.common.util.concurrent (7), com.google.common.math (6). The largest removals are com.google.common.collect (2), com.google.common.io (2), com.google.common.util.concurrent (1). Edge Jaccard among shared classes is 0.9677.


The [change-point audit](../results/change_points.json) lists every changed class and edge, source-JAR paths and source-entry checksums. A moved or renamed type can appear as a removal and an addition. New classes can support existing functionality. Annotation changes can affect the inventory without adding annotation-application edges. These observations identify implementation changes; interpreting them as feature growth or architectural improvement needs further evidence.

## The recorded AI proposal

The preserved AI response groups all **594 classes into 18 named modules**. It has MQ **0.094303** on the full graph and **0.089526** after projection to retained classes. The model received names, package documentation and the latest dependency graph, so its information differs from the structural algorithms' feature vectors. Its module names offer a semantic explanation but are not proof of the intended architecture.

| Baseline | Graph | Baseline MQ | AI MQ | AI → baseline MoJoFM | Baseline → AI MoJoFM |
| --- | --- | --- | --- | --- | --- |
| A1 | full | 0.255299 | 0.094303 | 28.57 | 61.63 |
| A2 | retained | 0.241695 | 0.089526 | 32.85 | 63.18 |
| A3 | full | 0.178989 | 0.094303 | 32.52 | 61.63 |
| A4 | retained | 0.184844 | 0.089526 | 36.12 | 66.25 |

The AI proposal was recorded in the preceding instructor-extractor study. The present revision preserves its actual prompt, response and assignment; only the evaluation against the new baselines is refreshed. Input hashes establish that the same latest graph is being used. No new live model response is claimed. [Experiment record](../results/ai/experiment.json) · [Detailed reflection](ai_reflection.md)

## Course interpretation and verification

The class and dependency trends provide evidence of growth in the measured implementation. They can motivate questions about Lehman's continuing-change and increasing-complexity laws, but they do not prove those laws. Functional growth requires evidence about functionality, perceived quality requires user evidence, and claims about organizational effort require process data. Static recovery also cannot establish every reflective or runtime interaction, separate-build feasibility or intended design constraint.

The complete suite passed **91 tests**, covering extraction, merging, UE boundaries, clustering, selection, metrics and archive restoration. The independent audit passed **7,949,858 evidence checks with no failures**, recomputing saved measurements and verifying all 120 final partitions, the pilot, source scope and comparisons. Its assertion count is not a count of independently designed unit tests. An old checkout receipt applies only to its named commit. [Validation](validation.md) · [Reproduction](reproducibility.md)

Reproducible calculations can still depend on debatable modeling decisions. The ownership boundary, retained isolates, extractor coverage, feature geometry, broad or weak elbow behavior and macro averaging remain part of the explanation. The report and complete tables make those choices reviewable rather than treating a single score as the answer.
