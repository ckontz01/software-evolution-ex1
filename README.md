# Guava architecture evolution - EPL484 Project 1 (revised)

A reproducible study of **30 distinct major/minor Guava families**, from **10.0 (2011-09-28) to 33.7.2 JRE (2026-09-29)**. Each family contributes exactly one stable representative. Each version has one finalized protocol and the assignment's four required conditions: A1 ACDC/full, A2 ACDC/UE-filtered, A3 k-means/full and A4 k-means/UE-filtered. The series contains **120 final partitions**.

**Start with the [revised PDF report](report/guava_evolution_report_revised.pdf), [results explanation](docs/results_interpretation.md) and [oral-exam guide](docs/oral_exam_guide.md).** The [two-person roadmap](docs/commit_roadmap.md) assigns balanced review and development work. Preparation and revision are AI-assisted; students' contributions and dates must reflect work they actually perform.

## What changed after the methodological review

| Concern | Revised decision |
|---|---|
| Custom annotation-heavy graph | The **unmodified instructor DependencyExtractor JAR** is the sole source of primary class relationships. Supplemental ASM extraction supplies ownership, enclosing aliases and UE member evidence separately. |
| Repeated patch observations | Sample **30 distinct major/minor families** from 45, one stable representative each. |
| Public-suffix code ownership | Include Guava-owned `com.google.thirdparty.publicsuffix` implementation alongside `com.google.common`; genuine external libraries remain excluded. |
| Weak justification for k | A single middle-release inertia pilot selects k=40 for 554 classes; the final rule scales that calibrated granularity with graph size. |
| Course agreement metric | Add **MoJoFM in both directions** for filtering, algorithm, temporal and AI comparisons; ARI remains supplementary. |
| Detector and MQ criticism | Retain the paper's standalone **UE**, without adding SIG, and the lecture-supported loop-free MQ formula. Explain those choices explicitly. |

The full original study is preserved at commit [`d970305`](https://github.com/ckontz01/software-evolution-ex1/tree/d970305d4c5c5302e4692ffc6ea8f0607de9ab82). Compact original tables/configurations are under [results/baseline_v1](results/baseline_v1). The revision changes several study choices together, so whole-study metric differences are not attributed to a single cause.

## Main revised findings

| Measurement | Guava 10.0 | Guava 33.7.2 |
|---|---:|---:|
| Canonical project-owned type nodes | 317 | 594 |
| Primary directed internal dependencies | 1,289 | 2,750 |
| Nonannotation types | 311 | 563 |
| Owned annotation types | 6 | 31 |
| Graph isolates, including annotation isolates | 15 | 45 |
| Code lines in graph-owned source files | 48,821 | 96,546 |

Class nodes increase by **87.4%** and primary dependencies by **113.3%**. These are measurements of a static implementation view, not direct measurements of functionality or design quality. The separate [source inventory](data/provenance/source_inventory_33.7.2.json) counts 610 owned Java files and 96,622 code lines including package descriptors; that population differs from the files linked to graph nodes.

![Class and dependency evolution across thirty distinct Guava families](results/figures/01_classes_dependencies.png)

At 33.7.2 the broader supplemental model contains 3,982 edges, while the normalized instructor graph contains 2,750. The 1,232 supplemental-only edges include 1,145 targeting annotation types. Those edges are preserved for comparison and **are not added to the primary graph**. All 31 owned annotation types remain as isolates in this latest graph. The [extractor comparison](data/graphs/33.7.2/extractor_comparison.json) makes these distinctions inspectable.

UE removes **22 of 594 classes**, leaving **572 nodes and 1,724 edges**. The classification preprocesses an architecture graph; it does not recommend deleting useful classes such as `Preconditions` or `ImmutableList` from Guava. [Worked member-evidence cases](docs/ue_case_study.md) explain actual removal/retention decisions.

| Latest condition | Nodes | Clusters | Cohesion | Coupling | Lecture MQ |
|---|---:|---:|---:|---:|---:|
| A1 - ACDC/full | 594 | 135 | 0.257500 | 0.002201 | 0.255299 |
| A2 - ACDC/filtered | 572 | 149 | 0.243079 | 0.001384 | 0.241695 |
| A3 - kmeans/full | 594 | 43 | 0.185154 | 0.006165 | 0.178989 |
| A4 - kmeans/filtered | 572 | 43 | 0.205205 | 0.003123 | 0.202082 |

**Filtering does not help every method under the declared metric.** After projecting each full partition onto exactly the retained graph, ACDC reclustering has lower MQ in **all 30 releases** (mean change **-0.023837**). K-means reclustering improves MQ in **29 of 30** (mean change **+0.020553**). The latest fair changes are **-0.004721** and **+0.038313**, respectively. These revised findings differ substantially from the original study. They are reported without adjusting the sample or detector to improve a result. [Same-graph comparisons](results/same_graph_comparisons.csv)

The primary graph has more isolates than the broader custom graph. ACDC restores isolates as singleton clusters, which have zero cohesion; its latest full partition has 135 clusters and 47 singletons. K-means has 43 clusters. Higher MQ therefore must be interpreted alongside granularity and the actual grouping, not as proof of intended-architecture accuracy.

### Directional agreement

| Latest comparison, identical retained universe | Forward MoJoFM | Reverse MoJoFM | ARI |
|---|---:|---:|---:|
| Projected A1 → A2 | 81.41 | 80.98 | 0.6025 |
| Projected A3 → A4 | 62.73 | 61.45 | 0.4297 |

MoJoFM scores are on a 0-100 scale; reversing the source/reference partitions can change the distance and normalization. An expert ground truth is necessary for an accuracy claim, but not for calculating agreement. All **178 classical comparison pairs** and their universes are saved in [partition_comparisons.csv](results/partition_comparisons.csv), with exact distance/normalizer details per release. [MoJoFM method](docs/mojofm.md)

All 30 size rows are in [sizes.csv](results/sizes.csv); all 120 metric rows and complete cluster/pair terms are preserved. The fresh latest-version AI experiment assigns all **594 classes to 18 conceptual modules**, with full-graph MQ **0.094303** and retained-graph MQ **0.089526**. AI → A1 MoJoFM is **28.57**, while A1 → AI is **61.63**; both directions matter because granularity and allowed move/join operations differ. The exact revised inputs, prompt, response and evaluations are preserved under [results/ai](results/ai). See [AI reflection](docs/ai_reflection.md) for responsibilities, evidence and limits.

## Reproduce the data and results

Use Python 3.12 and Java 17+. `EVOLUTION_JAVA` may point to the Java executable if it is not on PATH. Python dependencies are pinned in `requirements.lock.txt`; the included Eclipse compiler means a separate `javac` installation is not required.

```bash
git clone https://github.com/ckontz01/software-evolution-ex1.git
cd software-evolution-ex1
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python scripts/select_versions.py --check
python scripts/unpack_data.py
python scripts/fetch_tools.py
python scripts/fetch_data.py --offline --verify-git
python scripts/run_checks.py
python scripts/validate_results.py
```

The deterministic archives preserve the original JAR/source/POM artifacts and complete detailed results. Unpacking verifies archive/member hashes and refuses to overwrite differing files. The [archive manifest](archives/manifest.json) enumerates the exact contents. The revised 90 Maven artifacts total **120.407 MiB**. Source-to-Git correspondence is checked at both endpoints (326 and 611 Java files); intermediate source artifacts have SHA-256 pins without a claim of complete per-file Git comparison.

To repeat the study into separate output directories:

```bash
python scripts/run_study.py --phase all --graph-root data/recomputed_graphs --output results/rerun/recomputed
```

This compiles/prepares the tools, builds each normalized instructor graph and supplemental member evidence, constructs the fixed feature universe, repeats the one-release pilot and runs A1-A4. Wall times and environment metadata will change. The independent validator audits the canonical restored study; replacing canonical results intentionally requires regenerating dependent evidence and the report.

After restoring or recomputing canonical results:

```bash
python scripts/benchmark_ue.py
python scripts/audit_ue_cases.py
python scripts/audit_change_points.py
python scripts/evaluate_ai.py
python scripts/build_report.py
```

The final command writes `report/guava_evolution_report_revised.pdf` and an identical canonical copy `report/guava_evolution_report.pdf`. It reads saved results and fails on missing data or inconsistent configuration hashes; it does not invent measurements or generate new partitions. The AI evaluation scores an already recorded partition, rather than silently repeating a live model call.

## Pilot-calibrated k and manual control

The middle selected release is **25.1**, with **554 nodes and 2,681 edges**. The fixed candidate grid is `2, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 110, 130`. The normalized inertia chord-gap rule selects **k=40**, targeting about **13.85 classes per cluster**. The final rule is:

$$
k_{full}=\left\lceil\frac{40n_{full}}{554}\right\rceil,
\qquad k_{filtered}=\min(k_{full},n_{filtered}).
$$

It gives **k=23-45** across the selected full graphs. The elbow is broad: nearby candidates have similar normalized gaps. This is empirical pilot evidence plus an explicit scaling assumption, not a guarantee of the true component count. The declared fallback was not needed. MQ does not enter selection, and the final versions receive no separate k sweep.

A matched-ACDC-k diagnostic on the pilot shows why granularity matters: k-means MQ rises from 0.160308 at 40 clusters to 0.242393 at 110 clusters, while ACDC's 110-cluster MQ is 0.319277. Equal k does not equal identical cluster-size distributions or semantic quality. The matched trial is not used to select k. [Complete pilot decisions and curve](docs/pilot_decision.md)

To choose k yourself for a separate exploratory run:

```bash
python scripts/explore_release.py --version 33.7.2 --k 40 --acdc-size 20 --usage-threshold 0.85 --cardinality-threshold 0.90 --output results/rerun/my_k40
```

## Standalone JNode-UE

The new detector implements Yano and Matsuo's **Usage Equality** method from the supplied *Moderate Detection and Removal of Omnipresent Modules in Software Clustering* paper. The paper compares UE against the older significance-based JNode. This implementation does not add the old SIG predicate; UE intersected with SIG would be a separate hybrid.

```bash
python scripts/jnode_ue.py --classes data/graphs/33.7.2/classes.csv --members data/graphs/33.7.2/member_dependencies.csv --output results/rerun/ue_demo
```

The detector preserves original member identities through class merging, counts distinct source members separately from caller classes, and evaluates usage equality ≥0.85 and cardinality ≥0.90 inclusively. Classes without incoming member evidence are retained with an explicit reason. Removal is simultaneous, with no cascade. “External member” in the paper means outside the target class, inside the scoped project; external libraries remain excluded. [Equations and boundaries](docs/omnipresent.md)

Set aggregation and indexed lookups avoid all-pairs shortest paths. The [synthetic benchmark](results/performance/ue_benchmark.json) records actual times, expected-score checks and environment qualifications. Detector-only timing is distinct from extraction and CSV parsing; no speedup against the old JNode executable is claimed.

## Graph and feature policy

The instructor extractor's seven tutorial categories are normalized through the supplemental enclosing-class alias map. The metric graph is a binary directed union, with one edge per ordered pair, no self-loops and both endpoints internal. Raw category/occurrence evidence is preserved. The instructor receives a deterministic subset JAR of unchanged owned base class bytes; the complete Maven input is retained separately.

Project-owned `com.google.common` and `com.google.thirdparty.publicsuffix` types remain nodes, including annotations and isolates. JDK, failureaccess and external libraries are excluded. Genuine inner/nested/local/anonymous types merge into their outermost owners using metadata rather than a blind `$` split. Base entries define the multi-release-JAR view. The tools inspect target bytecode without executing Guava, and do not claim to resolve every reflection or runtime-dispatch dependency.

All releases use **715 union identities and 1,430 fixed outgoing/incoming feature columns**. K-means receives sparse `[A+I,(A+I)^T]` rows, L2-normalized. Identity terms never enter graph edge counts or metrics. Missing/removed coordinates stay as zeros. Seed 484, ten initializations, Lloyd updates and fixed iteration/tolerance settings apply throughout. Package labels and AI assignments are not structural features.

The original York ACDC source is unchanged. Its reversible `.java` input mapping avoids file-basename collisions. True isolates are restored as singletons. The pilot's size-10/20/40 partitions are identical, so 20 is retained globally; later orphan adoption can exceed that phase's size limit.

## Lecture metrics and interpretation

The reconstruction lecture permits both squared and loop-free cohesion denominators. We retain the loop-free form used in its worked example:

$$
A_i=\frac{\mu_i}{n_i(n_i-1)},\qquad E_{ij}=\frac{\epsilon_{ij}}{2n_in_j},\qquad
MQ=\frac1k\sum_iA_i-\frac{2}{k(k-1)}\sum_{i<j}E_{ij}.
$$

`epsilon` counts both directions. Singleton cohesion, the single-cluster coupling term and empty-graph metrics use explicit zero conventions. All unordered pairs, including zero-edge pairs, enter the coupling average. Per-cluster/pair CSVs preserve every term. Supplementary weighted cohesion and inter-edge fraction expose different aspects of granularity.

Static partitions describe implemented structure. They do not establish intended design, requirements satisfaction, user-perceived quality or architectural erosion. Lehman's laws are discussed within the evidence available. MoJoFM/ARI are agreement measures here, and the AI experiment has a different information setting because it also sees names and documentation.

## Selected releases

```text
10.0, 12.0.1, 13.0.1, 15.0, 16.0.1, 18.0, 19.0, 21.0
22.0, 23.1, 23.2, 23.4, 23.5, 24.0, 24.1, 25.1
26.0, 27.1, 28.0, 28.2, 29.0, 30.1.1, 31.0.1, 32.0.1
32.1.3, 33.1.0, 33.2.1, 33.4.8, 33.5.0, 33.7.2
```

The selector reconstructs the 30 family ranks from the captured 45-family catalog, independent of graphs and quality. It uses the highest eligible stable patch per selected family, with the declared oldest-boundary 10.0 exception. Some selected families are adjacent; spacing is by family rank rather than uniform calendar gaps. The [selection guide](docs/project_selection.md), [acquisition guide](docs/data_acquisition.md) and [manifest](config/versions.json) record exact decisions and evidence.

## Evidence and navigation

| Path | Contents |
|---|---|
| `third_party/dependency_extractor/` | Exact supplied instructor JAR, hash and launcher provenance |
| `java/DependencyExtractor.java` | Supplemental ownership, enclosing metadata, member evidence and separate sensitivity graph |
| `src/evolution/` | Normalization, UE, clustering, k selection, lecture metrics, MoJoFM and runner |
| `tests/` | Focused compiled Java, detector, clustering, metric and agreement tests |
| `archives/` | Original artifacts and complete detailed evidence |
| `data/provenance/` | Family selection, acquisition, inventory and Git/source checks |
| `data/graphs/VERSION/` | Instructor inputs/raw output/normalization and separate supplemental data |
| `results/*.csv` | Complete size, quality, runtime, temporal and agreement tables |
| `results/validation.json` | Independent audit of the current recorded study |
| `results/ai/` | Fresh revised-input AI prompt, response, partition and evaluation |
| `results/baseline_v1/` | Original configuration and summary results for transparent comparison |
| `results/figures/` | PNG and SVG figures generated from saved measurements |
| `docs/` | Methods, course references, worked examples and oral/contribution guides |
| `report/` | Revised PDF, generator-input hashes and render verification |

The requested temporary repository is the preparation destination. The teacher-owned repository URL and teammate identity were not supplied; teacher import and Blackboard submission are separate administrative actions. The roadmap describes genuine future review/development commits by both students, without fabricated authors or backdated activity.
