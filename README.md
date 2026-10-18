# Guava architecture evolution - EPL484 Project 1

A reproducible study of **30 distinct major/minor Guava families**, from **10.0 (2011-09-28) to 33.7.2 JRE (2026-09-29)**. Each family contributes exactly one stable representative. Each version has one finalized protocol and the assignment's four required conditions: A1 ACDC/full, A2 ACDC/UE-filtered, A3 k-means/full and A4 k-means/UE-filtered. The series contains **120 final partitions**.

**Start with the [revised PDF report](report/guava_evolution_report_revised.pdf), [results explanation](docs/results_interpretation.md) and [oral-exam guide](docs/oral_exam_guide.md).** The [two-person roadmap](docs/commit_roadmap.md) assigns balanced review and development work. Preparation and revision are AI-assisted; students' contributions and dates must reflect work they actually perform.

## Current study configuration

The third configuration follows the request to spread the versions through the release history and use the lecture's agreement measure. It covers every major version from 10 through 33, retains the latest endpoint, and adds five minor releases through a fixed calendar-gap rule. The shortest interval is 74 days. No major/minor family is repeated.

The unmodified instructor extractor remains the source of primary edges. Guava-owned public-suffix code, isolated owned types and annotation declarations stay in the inventory; external libraries and supplemental annotation-application edges stay outside the graph. Usage Equality, the feature-construction method and the k-selection strategy are unchanged. The new sample receives its own class-coordinate union, middle-release pilot and complete final run. Current partition agreement uses **MoJoFM in both directions**; quality uses **cohesion, coupling and MQ**.

The first study remains at commit [`d970305`](https://github.com/ckontz01/software-evolution-ex1/tree/d970305d4c5c5302e4692ffc6ea8f0607de9ab82), with summaries under [results/baseline_v1](results/baseline_v1). Later configurations remain in Git history. They are different studies, so their overall changes cannot all be attributed to one factor.

## Main findings

| Measurement | 10.0 | 33.7.2 |
| --- | --- | --- |
| Owned canonical types | 317 | 594 |
| Directed internal dependencies | 1289 | 2750 |
| Annotation types | 6 | 31 |
| Isolated nodes | 15 | 45 |
| Code lines in graph-owned source files | 48821 | 96546 |

Class counts increase by **87.4%** and dependencies by **113.3%**. These are counts of the extracted implementation, not direct measures of functionality or design quality. The complete [size table](results/sizes.csv) contains all 30 releases.

![Class and dependency counts through the sampled Guava releases](results/figures/01_classes_dependencies.png)

The latest full graph contains **594 nodes and 2,750 edges**. Usage Equality removes **22 classes**, leaving **572 nodes and 1,724 edges**. Filtering changes the graph used for analysis; it does not recommend deleting utility classes from Guava. [UE cases](docs/ue_case_study.md)

| Condition | Nodes | Clusters | Cohesion | Coupling | MQ |
| --- | --- | --- | --- | --- | --- |
| A1 | 594 | 135 | 0.257500 | 0.002201 | 0.255299 |
| A2 | 572 | 149 | 0.243079 | 0.001384 | 0.241695 |
| A3 | 594 | 43 | 0.185154 | 0.006165 | 0.178989 |
| A4 | 572 | 43 | 0.188325 | 0.003480 | 0.184844 |

To compare filtering fairly, the full partition is first restricted to the same retained classes and edges. The table counts whether reclustering that retained graph raises or lowers MQ.

| Method | Higher MQ | Lower MQ | Mean change | Latest change |
| --- | --- | --- | --- | --- |
| ACDC | 0 | 30 | -0.023655 | -0.004721 |
| k-means | 29 | 1 | +0.021299 | +0.021075 |

The effect depends on the algorithm and the measured graph. Higher MQ does not establish the intended architecture. Cluster counts and sizes also matter: the latest ACDC/full partition has **135 clusters**, compared with **43** for k-means/full. [All 120 measurements](results/metrics.csv) · [Same-graph comparisons](results/same_graph_comparisons.csv)

### Agreement between partitions

| Comparison | Classes | Forward MoJoFM | Reverse MoJoFM |
| --- | --- | --- | --- |
| A1 → A2 | 572 | 81.4079 | 80.9783 |
| A3 → A4 | 572 | 60.4356 | 58.3636 |
| A1 → A3 | 594 | 43.7063 | 41.1150 |
| A2 → A4 | 572 | 47.1869 | 42.7798 |

MoJoFM is on a 0–100 scale. Both directions are reported because reversing the source and reference can change the required moves/joins and the normalizer. For A1→A2 and A3→A4, the full partition is restricted to retained classes first. These are agreement scores, not accuracy against a validated intended architecture. [All 178 classical comparisons](results/partition_comparisons.csv) · [Method](docs/mojofm.md)

The recorded AI proposal assigns **594 classes to 18 modules**. Its MQ is **0.094303** on the full graph and **0.089526** on the retained graph. This is the original response from the preceding instructor-extractor study, now compared against the current baselines; no new AI recovery is claimed. Its original graph inputs, prompt, response and assignment remain unchanged. [AI record](results/ai) · [Reflection](docs/ai_reflection.md)

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

The deterministic archives preserve the original JAR/source/POM artifacts and complete detailed results. Unpacking verifies archive/member hashes and refuses to overwrite differing files. The [archive manifest](archives/manifest.json) enumerates the exact contents. The current 90 Maven artifacts total **116.252 MiB**. Source-to-Git correspondence is checked at both endpoints (326 and 611 Java files); intermediate source artifacts have SHA-256 pins without a claim of complete per-file Git comparison.

Version and pilot ZIPs are stored as `.zip.b64` text files; the endpoint Git-source bundle remains one ZIP. The same unpack command decodes the text automatically and verifies the stored file, decoded ZIP and each member before restoring the normal directory structure. Encoding preserves the original binary bytes. [Archive format](archives/README.md)

The complete test run passed **91 tests**. The independent result audit passed **7,949,858 evidence checks with no failures**, covering all 120 final partitions. Those totals describe different checks: the audit count includes repeated assertions over saved classes, members, edges and metric terms. [Validation scope and limits](docs/validation.md)

A fresh clone of [the published revision `ed18113`](https://github.com/ckontz01/software-evolution-ex1/commit/ed18113b1641481585ca9695312842d05d903a70) also passed the complete verification sequence. It restored all 2,385 archived files and reproduced all 62 checked deterministic files for the latest release byte for byte. The [verification receipt and command logs](results/reproducibility_v3/README.md) record the exact tested commit, environment and scope.

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

The middle release is **25.0**, with **554 classes**. The candidate grid is `2, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 110, 130`. The normalized endpoint-chord rule selects **k=40**, with gap **0.189102**. The final rule is:

$$
k_{full}=\left\lceil\frac{40n_{full}}{554}\right\rceil,
\qquad k_{filtered}=\min(k_{full},n_{filtered}).
$$

The pilot represents about **13.85 classes per cluster**; the final full graphs have **23–45 clusters**. The candidate with the largest interior normalized gap is selected if the gap is at least 0.02, with smaller k resolving exact ties. Otherwise the method uses the tested candidate nearest to 30. The recorded decision is `maximum_normalized_chord_gap`. MQ does not enter the choice. [Complete pilot curve and decisions](docs/pilot_decision.md)

The course asks for the number of groups to be explained. It does not prescribe a one-release elbow or size scaling. Keeping the same seven relationship types is a separate feature-selection decision. This study keeps its earlier k-selection strategy, but reruns the pilot because the new release cohort changes the middle release and feature-coordinate union. There is one pilot sweep, followed by one final A3/A4 partition per release and condition. The resulting k is a defensible study choice, not a known count of true modules.

To choose k yourself in a separate exploratory run:

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

The original York ACDC source is unchanged. Its reversible `.java` input mapping avoids file-basename collisions. True isolates are restored as singletons. The pilot checks size 10, 20 and 40; the declared final setting remains 20. The measured pilot comparison is recorded separately, and later orphan adoption can exceed that phase's size limit.

## Lecture metrics and interpretation

The reconstruction lecture permits both squared and loop-free cohesion denominators. We retain the loop-free form used in its worked example:

$$
A_i=\frac{\mu_i}{n_i(n_i-1)},\qquad E_{ij}=\frac{\epsilon_{ij}}{2n_in_j},\qquad
MQ=\frac1k\sum_iA_i-\frac{2}{k(k-1)}\sum_{i<j}E_{ij}.
$$

`epsilon` counts both directions. Singleton cohesion, the single-cluster coupling term and empty-graph metrics use explicit zero conventions. All unordered pairs, including zero-edge pairs, enter the coupling average. Per-cluster/pair CSVs preserve every term. Supplementary weighted cohesion and inter-edge fraction expose different aspects of granularity.

Static partitions describe implemented structure. They do not establish intended design, requirements satisfaction, user-perceived quality or architectural erosion. Lehman's laws are discussed within the evidence available. MoJoFM are agreement measures here, and the AI experiment has a different information setting because it also sees names and documentation.

## Selected releases

```text
10.0, 11.0, 12.0, 13.0.1, 14.0, 15.0, 16.0, 17.0
18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0
26.0, 27.0, 27.1, 28.0, 28.2, 29.0, 30.0, 31.0
31.1, 32.0.0, 33.0.0, 33.4.0, 33.5.0, 33.7.2
```

The selector uses the first eligible .0 release of each of the 24 major versions, with 13.0.1 as the documented ambiguous-tag exception, and preserves 33.7.2 as the latest endpoint. Five additional minor releases maximize the reduction in squared calendar gaps, subject to a 60-day minimum and at most two optional additions per major. The actual gaps range from **74 to 471 days**, with median **141 days**. Adjacent labels need not mean closely spaced dates: 33.4.0 and 33.5.0 are **275 days** apart. [Selection method and all dates](docs/project_selection.md) · [Manifest](config/versions.json)

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
| `results/ai/` | Preserved AI prompt/response/partition and current baseline evaluation |
| `results/baseline_v1/` | Original configuration and summary results for transparent comparison |
| `results/figures/` | PNG and SVG figures generated from saved measurements |
| `docs/` | Methods, course references, worked examples and oral/contribution guides |
| `report/` | Revised PDF, generator-input hashes and render verification |

The requested temporary repository is the preparation destination. The teacher-owned repository URL and teammate identity were not supplied; teacher import and Blackboard submission are separate administrative actions. The roadmap describes genuine future review/development commits by both students, without fabricated authors or backdated activity.
