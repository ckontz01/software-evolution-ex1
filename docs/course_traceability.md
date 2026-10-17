# Course material, decisions and oral-examination traceability

This study concerns **google/guava**, as selected by the students. Its purpose is
to reconstruct and evaluate the evolution of a static structural architecture.
This document separates requirements and taught concepts from the engineering
choices used to make the experiment reproducible. Numerical findings belong in
the generated results and report; they are not inferred from the lecture examples.

## Reading inventory and reference convention

The material review preceded implementation. All extracted text of the following
documents was read. References use PDF pages; where printed slide numbers differ,
both are supplied. Some examples/tool screenshots contain visual content that is
not completely represented by text extraction, so text coverage is not a claim
that every screenshot was independently transcribed.

| Reference | Course source | Complete coverage and topics |
|---|---|---|
| AS | `epl484.fall26.project1instr.pdf` | All 5 pages: groups, eligibility, data, four recovery conditions, evaluation, AI, report and submission. |
| TUT | `epl484.fall26.project1tutorial.pdf` | All 12 pages: procedure, relationship types, ACDC parameters/output, clustering and library documentation. |
| L12 | `lecture-1-2-Introduction.pdf` | All 50 pages: pp. 1–14 course/pair work; 15–22 maintenance/evolution; 23–28 co-evolution, maintenance types and ripple effects; 29–33 S/P/E systems; 34–48 all eight Lehman laws and their limitations; 49–50 conclusion/references. |
| L3 | `Lecture3-Requirements-Part1.pdf` | All 38 pages: pp. 1–8 requirements/change; 9–20 ambiguity, SMART and partial automated checking; 21–26 instability/modularity; 27–33 relationship types and traceability graphs; 34–37 inconsistencies; 38 summary. |
| L4 | `Lecture4-Requirements-Part2.pdf` | All 33 pages: pp. 1–9 changing features/documents; 10–20 traceability, matrices and visualizations; 21–31 feedback, CrowdRE and ALERTME with limitations; 32–33 conclusion/references. |
| L5 | `Lecture5-ArchitectureEvolution.pdf` | All 34 PDF pages: architecture definitions/views, drift/erosion, reverse engineering, bytecode dependency graphs, smells and their evolution. Printed slide 6 is absent: PDF p. 6 is slide 7, and subsequent printed slide numbers are one higher. |
| L67 | `Lecture6-7-ArchitectureReconstruction.pdf` | Reconstruction algorithms, features, clustering and evaluation reviewed in the companion architecture/method review. The implemented lecture MQ definition is made explicit below. |
| UE | `Moderate_Detection_and_Removal_of_Omnipresent_Modules_in_Software_Clustering.pdf` | The supplied five-page paper is the authoritative method source for the replacement JNode/Usage Equality detector. Equations 1–3 and thresholds are on PDF p. 2 / printed p. 663; the procedure and real examples are on PDF p. 3 / printed p. 664. These references were checked directly against the supplied PDF. |

The supplied old JNode executable is not used as the correctness oracle for the
replacement. The original ACDC implementation is used, with its source archive
and download receipt preserved under `third_party/acdc`.

## Requirements mapped to implementation and evidence

| Requirement or teaching | Source | Implementation / review evidence |
|---|---|---|
| Java, GitHub, at least ten major/minor versions, latest at least 10,000 LOC, nonarchived, nonfork, pre-2024 creation, fifty commits from 2024-01-01 | AS p. 1 | Version manifest and eligibility evidence under `config` and `data/provenance`. Thirty selected releases are the students' stronger sampling requirement. |
| Explain data collection, exclusions and cleaning | AS pp. 2, 4; L12 p. 8 | Artifact URLs, tag/commit identities, checksums, raw/canonical class counts and per-release extraction provenance. |
| Table and evolution graph of classes | AS p. 2 | Generated `results/sizes.csv` and report figures. Dependency-count figures are an additional student requirement. |
| Seven class relation types | TUT p. 6 | Extractor and documented relation policy; no arbitrary relationship weights are attributed to the slides. |
| Recover with and without omnipresent classes | AS pp. 2–3 | Replacement paper-based detector; A2/A4 operate on the induced internal graph of retained classes. |
| ACDC and a clustering algorithm, both graph conditions | AS p. 3 | A1=ACDC/full, A2=ACDC/filtered, A3=KMeans/full, A4=KMeans/filtered. Exactly one final output per condition per release. |
| Inspect ACDC main/parameters and investigate supported patterns and maximum size | TUT pp. 7–8 | Original `ACDC.java`; a one-version pilot; explicit `+so` and `-l20` final configuration unless a documented global pilot revision is made. |
| Document clustering library and k selection | AS p. 4; TUT pp. 10–12 | Sparse features and fixed heuristic below; fixed seed and explicit library parameters in execution metadata. |
| Cohesion, coupling and MQ for each output | AS p. 3; L67 PDF pp. 15–17 | `src/evolution/metrics.py`, hand-derived tests and complete cluster/pair terms. |
| AI recovery of latest version, including actual input/prompts/output | AS pp. 3–4 | Actual AI experiment record and latest-version comparison; no invented prompt history. |
| Explain results using course concepts and discuss limitations | AS p. 4 | Report discussion supported by L12/L3/L4/L5 and observed results. |
| Code, collected/calculated data and documented implementation; PDF report | AS pp. 4–5; TUT p. 3 | Repository artifacts and PDF; Blackboard is the report submission destination. |
| Two students contribute equally and explain their work | AS pp. 1, 5; L12 pp. 5–9 | Authentic contributions, review responsibilities, commit roadmap and oral guide. A planned contribution is not represented as already completed. |

### Resolving the notes consistently

The written assignment explicitly defines four conditions. The note “one
architectural analysis per version” is implemented as one **final configuration
and recovered architecture per condition**, after the pilot; it does not remove
the A1–A4 comparison. KMeans' internal initializations yield one selected fitted
partition, not additional reported architectural experiments.

The project tutorial gives **23 October, 23:59** (TUT p. 2). The introductory
course timetable labels its schedule tentative and lists 22 October (L12 p. 5).
The project-specific tutorial is the working deadline; students should follow any
subsequent explicit announcement. Teacher project approval is not established by
this repository or by automated eligibility checking.

## Structural model and feature choices

L5 PDF p. 9 / slide 10 distinguishes intended, described and implemented
architecture and static/dynamic views. This experiment studies a static view of
the implemented internal classes. Nodes are canonical project classes; an edge
`A -> B` means class A depends on B. L5 PDF pp. 22–23 / slides 23–24 teach this
bytecode/graph approach, including child-to-parent and implementation-to-interface
direction.

The student notes additionally require merging nested/anonymous classes and
excluding external libraries. These are explicit study boundaries. They do not
mean that the original program lacks external interactions or that removed
analysis nodes have been deleted from the real program. The manifest remains the
authority for internal nodes, including isolates.

For KMeans, let U be the sorted union of canonical class names over the thirty
selected versions, and A the directed binary adjacency of the current retained
graph. Rows correspond to current classes. Columns use the same U coordinates
for every run, outgoing coordinates first and incoming coordinates second:

\[
X = [A+I,\ (A+I)^T].
\]

Every row is normalized to unit Euclidean length. The identity entries represent
self-similarity for clustering features. **They are not dependency edges**, and
are never used in the Noise input or metric calculation. Absent or removed classes
keep their column positions, with zero evidence in both halves. The filtered graph
contains neither outgoing nor incoming dependencies involving a removed class.

This representation uses direction and structural neighbourhoods. It does not
provide package labels, a desired architecture or an AI partition as input to
KMeans. Sparse CSR storage avoids materializing the many zero cells. These exact
feature, identity and normalization rules are our engineering choices, consistent
with documenting the chosen representation; they are not a claim that the
lectures prescribe this unique matrix.

The final k rule is:

\[
k_{\mathrm{full}}=\max\left(1,\left\lceil\sqrt{n_{\mathrm{full}}/2}\right\rceil\right),
\qquad
k_{\mathrm{filtered}}=\min(k_{\mathrm{full}},n_{\mathrm{filtered}}).
\]

An empty retained graph has k=0 by convention. The full-version size determines
the value reused for A3/A4. This is a transparent granularity heuristic, not an
estimated optimum or a theorem taught in class. It avoids selecting k by the
same MQ later used for comparison. The pilot checks coverage and cluster-size
distribution; it does not perform a k sweep over thirty versions.

The fitted configuration uses scikit-learn KMeans with k-means++ initialization,
Lloyd iterations, `random_state=484`, `n_init=10`, `max_iter=300`, and `tol=1e-4`.
Names, input order and labels are canonicalized, and numerical thread pools are
limited to one thread. Actual library versions are recorded by the run manifest.
The official documentation defines the initialization/repetition/random-state
parameters and sparse input behavior:
[KMeans 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html)
and [normalize 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.normalize.html).
Identical feature rows can produce fewer distinct clusters than requested. The
implementation reports the actual number and warnings without inventing splits.

## What exactly the ACDC adapter does

The original source came from
[the author's York archive](https://www.eecs.yorku.ca/~bil/downloads/acdc.tar),
linked through the [course's ACDC page](https://wiki.eecs.yorku.ca/project/cluster/protected:acdc).
The archive SHA-256 is
`52755a6889a3f3f93cfe83f0a54639d62925442b54f8638f0dbd9d9ebdaf749c`.

The adapter calls the compiled original Java program. It passes real `call A B`
edges in an `.rsf` file. `+so` selects SubGraph Dominator followed by Orphan
Adoption. BodyHeader is omitted because the source explicitly matches C `.c/.h`
file pairs; that pattern supplies no class-level Java evidence here. The default
DownInducer produces a flat fine-grained decomposition.

The pilot exposed an input-identifier issue in applying this file-oriented tool
to Java class names. Upstream `Node.getBaseName()` removes the final dotted
suffix; bare names such as `p.A` and `p.B` therefore generate identical cluster
names `p.ss`. We reversibly append `.java` to every tool input node, so these
basenames become `p.A` and `p.B`. The adapter writes `node_id_map.csv`, passes
the exact same directed edges under those identifiers, and decodes memberships
before evaluation. This preserves the original algorithm and graph. A focused
real-Java regression with two disconnected cliques in the same package checks
that their recovered clusters stay distinct.

The `-l20` setting constrains SubGraph's cluster construction. It does **not**
guarantee every final cluster has at most twenty members. Subsequent Orphan
Adoption can enlarge clusters, and the original later ClusterLast step places
remaining orphans into `orphanContainer.ss`. Large final clusters are therefore
reported and discussed, not silently cut apart.

A dependency-only input cannot name a class that has no edges. The adapter records
those genuine graph isolates and restores each as a singleton outside the
unmodified Java algorithm. It fails if any class participating in a real edge is
missing from the returned partition. Duplicate memberships, unknown classes,
cycles in containment and malformed outputs are rejected. Old output files are
removed before invoking ACDC because some original argument/input errors use
`System.exit(0)`; a successful exit code alone cannot establish a successful run.

## Exact lecture metrics and an oral example

The metric formulas were checked directly against the rendered equations in
L67 PDF p. 15 and the worked example on p. 17; p. 16 explains their range.
Page 15 presents both n_i squared and n_i(n_i-1) cohesion denominators. We use
the latter, as in the page 17 example, because our directed graph excludes
self-dependencies. PDF pp. 46–47 discuss the earlier Noise detector and do not
define MQ.

Let C_i be a nonempty cluster, n_i its number of nodes and mu_i its directed
internal edge count. Let epsilon_ij count edges between C_i and C_j **in both
directions**. For k clusters:

\[
\operatorname{cohesion}_i =
\begin{cases}
\mu_i/[n_i(n_i-1)] & n_i>1,\\
0 & n_i=1,
\end{cases}
\]

\[
\operatorname{coupling}_{ij}=\epsilon_{ij}/(2n_i n_j),
\qquad
MQ = \frac1k\sum_i\operatorname{cohesion}_i
-\frac{1}{\binom{k}{2}}\sum_{i<j}\operatorname{coupling}_{ij}.
\]

For k=1, the coupling term is zero. For an empty graph, reported macro metrics
are zero by explicit convention. Zero-edge cluster pairs remain in the coupling
average. No cluster is omitted because it is a singleton or contains an isolate.

Example: C1={a,b}, C2={c,d}, with directed edges a->b, b->a, c->d, d->c, b->c.
Each cluster has cohesion 2/(2*1)=1. The cross-pair count is one and pair coupling
is 1/(2*2*2)=1/8. Thus macro cohesion=1, coupling=1/8 and **MQ=7/8=0.875**.
Adding a separate isolated singleton creates a third cluster with zero cohesion:
macro cohesion becomes 2/3, coupling becomes (1/8)/3=1/24, and MQ becomes 5/8.
This explains why coverage and singleton policies matter even when edges do not
change.

Supplementary fields report node-size-weighted cohesion, possible-pair-weighted
cohesion, the inter-edge fraction, graph density and cluster-size distribution.
They supplement the required macro formula; they do not replace it. Full and
filtered partitions are also compared on the same retained graph to distinguish
the effect of deleting edges from a change in the recovered grouping.

## How to interpret the study without overstating it

**Reconstruction is reverse engineering.** L5 PDF p. 14 / slide 15 defines reverse
engineering as recovering components, relations and higher-level representations.
This assignment does not modify Guava's implementation. L5 PDF pp. 18–19 / slides
19–20 also emphasize that different architectural views need different techniques.
ACDC, KMeans and AI can therefore produce different useful views without one being
established as the definitive intended architecture.

**Structural change alone does not prove erosion.** L5 PDF p. 12 / slide 13
distinguishes drift from decisions violating the intended architecture. Calling a
change erosion needs an intended design constraint and evidence of violation.
MQ and coupling are structural measurements, not direct measurements of user
satisfaction, performance or correctness. Choosing k independently is particularly
useful because k=1 removes the inter-cluster coupling term and MQ can favor coarse
partitions.

**Omnipresence is not the same as a hub smell.** L5 PDF pp. 27–30 / slides 28–31
cover unstable, hub-like, cyclic and God-component smells. The replacement JNode
must follow the supplied UE paper, not merely count high-degree nodes. Zero
detected omnipresent classes can be a legitimate method result.

**Connect Lehman's laws only to available evidence.** L12 p. 33 limits the
empirical laws to E-type systems; pp. 35–48 explain them and their limitations.
Class/dependency growth is consistent with continuing change and may indicate
increasing structural complexity. Stable or better modular structure amid growth
may be consistent with deliberate maintenance. However, class growth does not
prove functional growth (pp. 43–44); MQ does not measure the user-perceived quality
in the seventh law (p. 45); and thirty sparse releases cannot prove organizational
stability, self-regulation or all eight laws (p. 48). Sparse sampling omits
intermediate changes and release gaps need dates if discussing rates.

L12 p. 27 distinguishes corrective, adaptive and perfective maintenance; p. 28
explains impact analysis and ripple effects. A dependency is a possible change
propagation path, not evidence that a particular historical change propagated.
L12 p. 39 recommends plots/statistics and connecting changes with recorded logs or
refactoring activity. Specific causes need release-note or commit evidence.

**Use the requirements lectures for traceability and uncertainty.** L3 pp. 9–15
cover ambiguous/conflicting requirements and measurable statements. Their use here
is explicit definitions and an auditable checklist. L3 pp. 16–19 show false positives
in automated support: automatic evaluation still needs interpretation. L3 pp. 27–33
distinguish requirement relations and lexical similarity; these must not be mixed
with the seven bytecode relation types. Names supplied to AI are clues, not proof
of component functionality.

L4 p. 8 explicitly observes that major releases need not change every feature at
once. A structural plateau does not mean no development took place. L4 pp. 11–15
teach inter/intra-version and forward/backward traceability: each report claim
should connect to a source version, data-cleaning rule, graph, partition and metric
file. P. 13 states that traceability itself does not guarantee correct or complete
implementation. L4 pp. 22–31 cover user-feedback mining and its limitations; that
is background, not a requirement to add review mining to this structural study.

## Questions both students should be able to answer

1. What does Guava provide, and what evidence establishes every eligibility criterion?
2. Why were these thirty releases selected? Which releases/variants were excluded, and what can sparse sampling miss?
3. Which tag, commit, artifact URL and checksum identify a particular input?
4. What counts as a class, and how are nested, anonymous, generated, test and external classes handled?
5. How is each dependency category recognized, which direction does it have, and how are duplicates combined?
6. How does the replacement JNode implement the paper's equations, and which hand-worked cases validate it?
7. Why can a popular class fail omnipresence, and why can zero removed modules be valid?
8. What are A1–A4? What is fixed across releases and between full/filtered conditions?
9. What do `+so` and `-l20` mean in the original ACDC code? Why can the final orphan cluster exceed twenty nodes?
10. What exactly are the KMeans rows and columns? Why does a removed class have zero columns rather than shifting the schema?
11. Why this k rule, seed and initialization setting? What would require reconsidering the pilot decision?
12. Can you compute the 0.875 MQ example by hand, then explain the effect of adding an isolated singleton?
13. Which findings are observed, which are interpretations, and which Lehman laws are not measurable here?
14. What exact material did the latest-version AI experiment receive, what did it return and how was it checked?
15. Which work and reviews did each student actually perform, and can each reproduce and explain the full chain?
