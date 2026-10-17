# Analysis model and its limits: revised study

## Two extraction roles with an explicit boundary

The **unmodified instructor-provided DependencyExtractor JAR produces the primary class-dependency graph**. The supplied executable is checksum-pinned, its invocation and raw output are preserved, and a normalization adapter applies the same class ownership, enclosing-class aliases, duplicate removal and self-loop policy in every release.

The supplemental `java/DependencyExtractor.java` reader has a narrower role in the revised study: it establishes the complete source-owned class inventory, supplies bytecode enclosing metadata, and extracts resolved method/field member references required by the Usage Equality equations. Its broader class dependency output is audit evidence only. It does not add annotation-application edges, resolved-declaring-owner class edges or extra type edges to the primary instructor graph.

The instructor is launched through an explicit classpath using its original `CompCalc.MainClass` and unchanged bundled dependency JARs. This works around its Eclipse jar-in-jar launcher issue on Java 17 without patching its algorithm. The target input is a deterministic JAR containing only owned base `.class` entries copied byte for byte from the original binary; original retained-class hashes, the derived-input hash, command and output are saved. Tool dependencies are analysis-runtime libraries, not Guava graph nodes.

This distinction prevents accidental mixing of two dependency models. A class relationship extracted from a symbolic bytecode owner and a resolved declaration identity used by UE answer related but different questions. Both are recorded under their actual provenance.

## Scope: project-owned Guava production code

The subject is `google/guava`, specifically the published `com.google.guava:guava` production artifact. The study uses the unsuffixed Java artifact before 23.1 and `-jre` thereafter. Android, GWT, test libraries, test suites, benchmarks and separately distributed dependencies are outside the target variant.

Class ownership requires a corresponding source file in the matching source JAR under either:

- `com.google.common`
- `com.google.thirdparty.publicsuffix`

The second package contains Guava's own Java implementation and carries Guava Authors headers. The word `thirdparty` in its namespace does not establish external ownership. Its inclusion corrects the earlier namespace-only boundary. External JDK, failureaccess and annotation-library types are still excluded. A retained dependency must have both endpoints in the owned class universe. The same boundary applies to member evidence used by UE.

Stable **release versions** with alpha, beta, RC or snapshot suffixes are excluded. Guava's `@Beta` annotation concerns an API's compatibility status; it does not make the annotated class external or its stable release a beta distribution. Owned classes marked `@Beta` remain included.

## What one class means

The node inventory consists of owned top-level Java types: classes, interfaces, enums and annotation types, plus records if present. Genuine inner, nested, local and anonymous binary classes are merged into their outermost enclosing class using class-file `InnerClasses` and `EnclosingMethod` metadata. This avoids treating every legal dollar sign as a nesting marker. Every binary-to-canonical alias is preserved.

Original member identities include binary declaring owner, member kind, name and JVM descriptor. `Outer#run()` and `Outer$Inner#run()` therefore remain distinct members after their class owners merge. UE depends on these distinct source-member counts. Relationships that become internal to one canonical class are removed from the inter-class graph.

`module-info.class` and `package-info.class` are metadata descriptors, not architecture nodes. The inventory uses base entries of multi-release JARs rather than counting duplicate version-specific implementations. This is a declared base-bytecode view, not a reconstruction of the class body selected by every possible runtime.

All owned canonical types remain nodes even when no primary edges touch them. The class inventory and an edge list have different purposes: inferring all nodes from edge endpoints would silently discard isolates.

## Instructor relationship categories

All seven categories taught on tutorial page 6 are selected. We accept the relationship evidence emitted by the instructor tool, normalize endpoints and preserve a typed audit. We do not claim that every Java construct in a category is necessarily recognized by that executable.

| Category | Relationship direction in the primary graph |
|---|---|
| EXTENDS | Child type to parent type |
| IMPLEMENTS | Implementing class to interface |
| METHOD_CALL | Caller class to the target owner emitted by the instructor tool |
| METHOD_PARAMETER | Class using a method parameter type to that type |
| FIELD_REFERENCE | Class accessing a field to the owner emitted by the instructor tool |
| TYPE_USAGE | Class using a type to the referenced type recognized by the tool |
| EXCEPTION_THROWS | Class declaring a thrown exception to the exception type |

The graph is the **binary directed union** of selected categories: each ordered pair appears once, regardless of how many call sites or categories support it. Each typed pair also appears once in the category audit. Self-loops are removed after owner merging. No arbitrary frequency or fractional relation weights enter the lecture's bounded density formulas. No edge is introduced merely because two names share a package.

## Annotation policy and the reason for revision

The original custom graph treated annotations attached to declarations as type dependencies. This created large compatibility/nullness hubs that UE could not assess through member use. The revised graph uses the instructor baseline and **does not add supplemental annotation-application edges**.

An owned annotation type still belongs to the complete node inventory. It can be an isolate, affecting singleton counts and macro metrics, so the report breaks down annotation types, nonannotation types, isolates and annotation isolates. This is more explicit than hiding metadata types by deriving the node set from edges.

Ordinary class references involving an annotation type remain eligible when emitted by the instructor extractor. An annotation can affect program behavior: Guava's EventBus tests `Subscribe` and `AllowConcurrentEvents` through ordinary Java operations. Consequently, the policy does not equate all annotation-related code with irrelevant metadata. It also does not delete an API class just because that class is annotated.

## The paper-based detector replacement

The attached 2020 Moderate Detection paper proposes **Usage Equality (UE)** and compares it with the older JNode/Noise method. This project implements that requested paper as **JNode-UE**. It does not claim to reproduce the older ComponentRank/shortest-path significance detector, and it does not add SIG as a third predicate. UE intersected with SIG would be a separate hybrid requiring its own justification.

UE uses distinct, resolved internal field/method references. Structural-only relationships do not become invented member calls. The paper's “external members” are members outside the target class within the declared project scope; external libraries are not included.

In this implementation, the class fan-in denominator counts distinct caller classes in the resolved member-use graph. This is an explicit extraction convention. The source-member fan-in for each target member is a different quantity and remains distinct after owner merging. A target with no incoming member-use evidence is retained with undefined scores and a stated reason. The paper does not prescribe every Java extraction or zero-evidence boundary case.

The fixed thresholds are usage equality at least 0.85 and cardinality at least 0.90. Decisions are computed once against the original scoped evidence; all qualifying classes are removed simultaneously from the class graph. There is no cascade and no per-version threshold search. See [omnipresent.md](omnipresent.md) and [ue_case_study.md](ue_case_study.md) for equations and examples.

## One pilot, then one frozen protocol

The revised sample contains 30 distinct major/minor families, selected using release history alone. A pilot on the middle selected release examines ACDC subgraph sizes and a declared grid of k-means cluster counts. The final graph policy, UE thresholds, feature schema, algorithm options and calibrated k rule are fixed before the 30-release final run. The required A1–A4 outputs are one final partition per condition per release.

ACDC uses the original York implementation with `+so` and `-l20`. A reversible `.java` suffix on input IDs avoids its file-basename collision for bare Java names, then outputs are mapped back. Real graph isolates are restored as singletons because dependency-only RSF cannot name them. The subgraph-size setting is not a global bound on final cluster size; orphan adoption can produce larger groups.

K-means receives outgoing and incoming adjacency profiles in one sorted union of class coordinates. Its matrix is `[A+I,(A+I)^T]`, stored sparsely and row-L2 normalized. Identity entries are clustering features only: they never enter edge counts or quality metrics. Absent or removed classes keep their coordinate positions as zeros, and removed nodes have no rows. Package names and desired module labels are not numeric features.

The pilot chooses an inertia elbow from a declared candidate grid. Normalize k and inertia between their endpoint observations and choose the largest chord-distance elbow, with a deterministic tie rule (smaller k wins). A maximum normalized interior gap below 0.02 triggers the predeclared nearest-candidate fallback to k=30; this guard prevents claiming a clear elbow on a flat curve. Let the selected pilot contain `n_p` classes and `k_p` clusters. Every final full graph requests `ceil(n_full*k_p/n_p)` clusters; its filtered graph reuses that value, clamped only when fewer nodes survive. This is empirical pilot evidence plus a size-extrapolation assumption, not a lecture theorem or a guaranteed true component count. MQ is not the tuning objective. [pilot_decision.md](pilot_decision.md) records the actual values and limitations.

A fixed seed, ten k-means++ initializations, Lloyd updates, iteration/tolerance limits and one numerical thread make the process repeatable in the pinned environment. Internal initializations produce one fitted partition. A manual `--k` exploration uses a separate output directory and does not change the published series.

## Evaluation and valid conclusions

The required lecture formula uses directed loop-free cohesion `mu_i/[n_i(n_i-1)]` and pair coupling `epsilon_ij/(2*n_i*n_j)`, with the latter counting both directions. MQ is mean cohesion minus mean coupling over all unordered cluster pairs, including zero-edge pairs. The lecture allows an alternative `n_i^2` cohesion denominator; we retain the loop-free form used in its worked example. Singleton/empty conventions and complete per-cluster/pair terms are explicit.

Macro metrics depend on cluster granularity and isolates. Results therefore include cluster counts, maximum sizes, singleton counts, weighted cohesion and edge retention. ACDC and k-means need not produce matching numbers of clusters even after empirical k calibration. Higher MQ alone does not establish the intended architecture.

Full-versus-filtered agreement is evaluated on the same retained class universe: project the full partition before comparing it with the newly recovered filtered partition. Temporal comparisons use common class identities. MoJoFM is reported in both directions with a declared reference partition; ARI is supplemental symmetric agreement. These are valid agreement calculations without ground truth. Calling them recovery accuracy would require a validated reference architecture. See [mojofm.md](mojofm.md).

Static extraction does not recover arbitrary reflection, dynamic class loading, every runtime dispatch target or dependencies erased by constant inlining. Compiler changes can affect observable evidence. Member resolution has explicit missing/ambiguous diagnostics. The revised graph, scope, sampling and k policies change together, so a whole-study difference from the original run cannot identify the causal contribution of one change.

Class/dependency growth, MQ and partition stability characterize the measured implementation view. They do not directly measure feature growth, user satisfaction, organizational effort, runtime performance or architectural erosion. An erosion claim needs an intended design constraint and evidence of its violation. The course's Lehman discussion supplies questions and qualifications rather than an automatic conclusion from a chart.
