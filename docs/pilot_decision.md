# Pilot decision: Guava 28.2

**Decision:** retain original ACDC with `+so`, SubGraph size 20 and default fine
flat output; retain the predeclared KMeans k rule. Apply the corrected, reversible
ACDC filename encoding to every release. No parameter was selected separately
for individual final versions.

## Preselected input and purpose

The middle selected release, 28.2, was chosen before looking at quality scores.
Its scoped graph has 555 canonical classes and 3,550 directed binary internal
edges. The pilot checked ACDC size values 10, 20 and 40 and one KMeans fit with
k = ceil(sqrt(555/2)) = 17. It was intended to find coverage, representation and
cluster-size problems before the 30-release study, without a k sweep.

## A concrete problem caught and repaired

The original file-oriented ACDC implementation derives a cluster name from
`Node.getBaseName()`, which removes the last dot and everything following it.
Bare Java class IDs `p.A` and `p.B` therefore share the basename `p` and can
produce the same output container name `p.ss`. On the first adapter check,
different Guava dominators collapsed under package-level output labels: the
apparent partition had only 14 clusters, including one of size 222.

Those results were rejected as an identifier-compatibility failure. The adapter
now maps every class ID to `CLASS.java` only for the ACDC process. For example,
`p.A.java` and `p.B.java` preserve distinct basenames `p.A` and `p.B`. All graph
edges are mapped one-to-one, `node_id_map.csv` preserves the mapping, and output
memberships are decoded before evaluation. Original ACDC source is unchanged.

A real-Java regression with two disconnected three-class cliques in one package
now returns two separate clusters. The independent final audit verifies the
identifier map, the exact mapped edges and complete decoded membership in every
ACDC run. The failed preliminary adapter output is not included among the 120
final architectures.

## Corrected pilot evidence

| Method | Size setting / k | Clusters | Largest cluster | Singletons | MQ |
|---|---:|---:|---:|---:|---:|
| ACDC | 10 | 90 | 44 | 3 | 0.378543620 |
| ACDC | 20 | 90 | 44 | 3 | 0.378543620 |
| ACDC | 40 | 90 | 44 | 3 | 0.378543620 |
| KMeans | 17 | 17 | 60 | 0 | 0.076883981 |

The three corrected ACDC membership CSVs are byte-identical, with SHA-256
`38cd7c4e86fb504edb05d4a09f6bf8e7e834b7dc044f7dba5728da438a233eaf`.
The pilot therefore provides no evidence for preferring size 10 or 40 over 20.
It does not establish that the size parameter is irrelevant to every graph.
The size value controls a recovery stage; later adoption can enlarge clusters,
so 44 is not a violation of a global size-20 cap.

ACDC and KMeans have different granularity and objectives. Their pilot MQ values
are diagnostic observations, not a comparison at matched k and not a reason to
optimize KMeans k against the same metric later used for evaluation. KMeans keeps
the automatic rule `ceil(sqrt(n_full/2))`, with the full-version value reused for
its filtered condition. Sparse feature coordinates, identity terms, normalization,
seed and initialization count remain identical in policy across all releases.

## Frozen record

The canonical evidence is `results/pilot/pilot.json`, the three ACDC membership
CSVs, KMeans membership and run logs under `results/pilot/`. The corrected final
configuration is `config/analysis.json`, SHA-256
`c9cdafab5f35e5df2d1b9947a5b3fd0f3b5fca5cc51b60f26de1c64e2a8c6376`.
The final run manifest has this same configuration hash. The 30-release run
produces one final A1/A2/A3/A4 partition per release; the independent audit
recomputes measurements without generating additional architectures.

Tutorial PDF pp. 7–8 motivate examining the original ACDC main/options.
Architecture Reconstruction PDF pp. 15–17 define the reported lecture MQ.
Detailed implementation, metric choices and course connections are in
`docs/course_traceability.md`; final findings are in `docs/results_interpretation.md`.
