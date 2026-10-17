# Analysis model and its limits

## Scope: Guava production code

The subject is `google/guava`, specifically the published `com.google.guava:guava` production artifact. We sample stable JRE releases, using the unsuffixed Java artifact before the JRE/Android split and `-jre` afterwards. Android, GWT, test libraries, test suites, benchmarks and separately distributed dependencies are outside this fixed scope. A repository with multiple products should not be represented by concatenating variants or by counting test classes as production architecture.

Membership requires both a `com.google.common` binary name and a corresponding Java source file in the matching source JAR. This excludes JDK classes, annotation dependencies, `failureaccess`, other libraries, bundled `com.google.thirdparty` classes, and any explicitly shaded library namespace. Every retained class and every exclusion is recorded. A source-owned internal utility remains Guava code even if many Guava classes use it.

Stable **release versions** with prerelease suffixes such as alpha, beta, RC or SNAPSHOT are excluded. Guava's `@Beta` annotation concerns API compatibility and does not make a class an external library or the containing release a prerelease. Those source-owned classes are retained. Filtering them would silently remove part of Guava's published implementation.

## What one class means

The node inventory consists of source-owned top-level Java types, including classes, interfaces, enums, annotations and records when present. Inner, nested and anonymous binary classes are merged into their outermost enclosing class using class-file `InnerClasses` and `EnclosingMethod` metadata. This is more precise than assuming every dollar sign indicates nesting. The alias table records every merge.

The distinct original member identity includes the original declaring binary class, field/method kind, name and JVM descriptor. Thus `Outer#run()` and `Outer$Inner#run()` remain different members after their class owners are merged. This matters for UE's source-member counts. Dependencies that become intra-class after merging are removed from the inter-class graph.

`module-info.class` and `package-info.class` are metadata, not architecture nodes. For multi-release JARs, only base class entries are included. This yields a consistent base implementation view and avoids duplicate copies of the same class. It does not reconstruct the alternative version-specific runtime implementation selected by a newer JVM.

## Relationship definitions

All seven relation categories shown on tutorial slide 6 are retained. Each unique `(source, target, category)` appears once in the typed audit CSV. Their union is a binary directed graph: each ordered class pair appears once regardless of the number of categories or call sites. This preserves the bounded directed-density formulas taught in the reconstruction lecture.

| Category | Bytecode evidence retained | Interpretation |
|---|---|---|
| EXTENDS | Superclass; superinterfaces of an interface | Child depends on parent. |
| IMPLEMENTS | Interfaces implemented by a class | Implementation depends on interface. |
| METHOD_CALL | Method invocation and resolvable method-handle references, including constructors | Caller depends on the used method's internal declaring owner when resolvable. |
| METHOD_PARAMETER | Object/array element types in method descriptors, including invocation descriptors | A method/call refers to a parameter type. |
| FIELD_REFERENCE | Field read/write instructions and field handles | Caller depends on the field's declaring owner when resolvable. |
| TYPE_USAGE | Field/return types, generic signatures, annotations, allocation, casts, class constants, arrays and catch types | Structural type coupling visible in bytecode. |
| EXCEPTION_THROWS | Declared exception types on methods | Method owner depends on a declared exception type. |

The extracted relation is static. Virtual calls are not expanded to every possible runtime implementation. Reflection, service loading and dynamically assembled class names are not resolved. Compile-time-inlined primitive/string constants may leave no class reference in bytecode. Debug-only local variable information and stack frames are skipped to keep the model stable across compiler debug settings. These limitations are shared across all releases.

No fractional or frequency weights are used: the assignment permits choices, but supplies no empirical basis for declaring one category twice as strong as another. The typed table keeps that evidence available for a future sensitivity study. Such a study would be a different configuration and is not mixed into the 30-version series.

## The requested detector replacement

The attached 2020 Moderate Detection paper proposes **usage equality (UE)** and compares it with the older JNode/Noise method. They are different algorithms. This project implements the requested paper as **JNode-UE**, a replacement command-line tool, and labels the substitution explicitly. It does not claim to reproduce Constantinou et al.'s 2015 ComponentRank/shortest-path algorithm.

The paper requires member-level evidence. UE therefore uses resolved method/field member dependencies; structural-only relations do not become invented member calls. Its 'external members' means members outside the target class *within our scoped Guava project*, not external-library members. Each class is evaluated once using the original scoped member graph. All detected classes and their incident edges are removed simultaneously, without a removal cascade. See `omnipresent.md` for the exact equations and boundary examples.

## One frozen configuration

A pilot on the middle selected release examines ACDC subgraph-size settings. The final size rule, relationship selection, graph representation, UE thresholds, feature schema, random seed and k rule are fixed across the release series. The required A1/A2/A3/A4 results are one final partition per condition per release, not independent parameter sweeps at every version.

K-means uses outgoing and incoming adjacency profiles in a shared, sorted union of class coordinates. An identity entry is added so a directly related class pair can share neighborhood coordinates and isolated classes have a defined feature vector. These identity entries are features only; they never enter edge counts or quality metrics. Rows are L2-normalized. Removed classes have neither rows nor nonzero dependency columns in the filtered condition. Empty future-version coordinates contain zeros and supply no future dependency evidence.

We choose `k = ceil(sqrt(n_full / 2))`, reuse the full-version k in its filtered condition, and clamp only if fewer than k classes survive. This is an explicit engineering heuristic, not a theorem or a lecture-prescribed optimum. It provides comparable, gradually increasing granularity without optimizing k against the MQ later used for evaluation. Requested and actual cluster counts are recorded. Ten deterministic initializations within one k-means fit produce one final partition; they are not ten separately reported architectures.

## What can be concluded

The lecture metrics quantify static cohesion and coupling in a partition. They do not establish the intended architecture, correctness of design, runtime performance, feature growth or user-perceived quality. MQ is reported alongside its two components, cluster sizes and edge retention. In addition, comparisons on the same retained class set distinguish repartitioning from the easier graph produced by removing high-use nodes.

Package names can help interpret modules, but they are not independently validated architectural ground truth. Agreement metrics, where reported, mean agreement between two partitions, not recovery accuracy. Without a validated reference architecture, we do not invent a MoJoFM accuracy score. Sparse release sampling shows changes between observations; it does not locate the exact commit at which each change arose.
