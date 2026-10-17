# Oral examination guide

This guide explains the implemented study. It is not a script to memorize: open the referenced files, reproduce the worked examples, and follow a real release through the pipeline. Both students should understand the whole chain and be able to identify their actual contributions.

## 1. What question did we investigate?

We reconstructed a static structural view of Guava's production architecture over 30 spaced stable releases. We asked how its size and dependency structure evolved, what partitions ACDC and k-means recovered, and how excluding omnipresent classes affected those partitions. The latest release also has a separate AI-assisted recovery exercise.

The important qualification is **static structural view**. A class-dependency partition is evidence about the implementation. It is not a complete description of runtime processes, deployment, architectural intentions or design rationale. This distinction comes from the lectures on intended, described and implemented architecture.

## 2. Why Guava?

The team selected `google/guava`. The eligibility record verifies the assignment's conditions: Java, an active nonfork GitHub repository created before 2024, enough major/minor release families, sufficient recent commits, and more than 10,000 production code lines in the latest selected version. Use the measured values in `data/provenance/project_eligibility.json` and `results/sizes.csv`; do not quote a current GitHub statistic from memory.

Guava is itself a collection of libraries. 'Exclude external libraries' means exclude code outside the selected Guava production scope. It does not mean delete Guava's own collections, concurrency or I/O modules because they provide library functionality.

## 3. How did you choose the versions?

The current sample covers all 24 major versions from 10 to 33, using each major's first eligible .0 release. Version 13.0.1 is the exception because the 13.0 tags are ambiguous. The latest release, 33.7.2, fixes the other endpoint. Five additional minor releases fill the largest gaps in time, using a deterministic rule: choose the candidate that most reduces the sum of squared calendar gaps, require at least 60 days between observations, and allow at most two optional additions per major. Each family appears once. The actual gaps range from 74 to 471 days, with median 141. This replaced the earlier family-rank sample, which still put four 23.x releases within 56 days. The JRE artifact is used after the platform split; Android is not counted as a second historical observation. The selector reads release metadata only, never the results.

The release sample was chosen before evaluating clustering quality. We did not search for versions that made a detector or algorithm look better. The sample does not reveal every intermediate change or identify the exact commit responsible for a change between observations.

## 4. How did you get the data?

The release identity comes from the official GitHub repository. A tag name is a convenient label; the commit SHA fixes the source revision. Binary JARs, matching source JARs and POM files come from Maven Central under the official Guava coordinates. The POM documents the artifact and its dependencies; those dependencies are not downloaded as analysis inputs.

For every artifact we record its URL and SHA-256. The fetcher also checks Maven's published checksum. A SHA-256 does not prove that software is trustworthy; here it ensures a future rerun uses identical input bytes. Source-to-Git checks link published source artifacts back to pinned revisions and report generated-file or packaging differences explicitly.

Commands and artifacts to inspect: `scripts/fetch_data.py`, `config/versions.json`, and `data/provenance/`.

## 5. Why use bytecode? Did you execute Guava?

The assignment permits source, class files or JARs. Published bytecode avoids having to rebuild decades of releases with different historical build systems, while preserving real member descriptors, inheritance and invocation instructions. The instructor extractor reads class files to produce the primary class graph. Our supplemental ASM reader supplies owned-class/enclosing metadata and resolved member-level evidence for UE. These tools inspect Guava bytecode as data; they do not execute the target Guava program.

The Java process executes the instructor extractor, the supplemental reader and ACDC, not Guava's application code. Java 17 is the analysis runtime. Older class files are read as data. We use source JARs for ownership, code size and interpretation.

## 6. What is a class in your table?

A node is an owned top-level Java type: class, interface, enum, annotation or record when present. Compilers generate separate class files for inner, nested and anonymous classes. We merge these into the outermost enclosing type and record every alias. Therefore the raw binary-class count is larger than the node count.

The Java extractor uses enclosing metadata. A dollar sign alone is not a sufficient rule because it is legal in a top-level Java identifier. The integration fixture exercises both genuine nesting and this boundary.

`module-info.class` and `package-info.class` are metadata and are excluded. Isolated owned types remain in the node inventory even if they have no retained dependency edges.

## 7. How did you remove external dependencies?

Membership is defined before building the analysis graph: a retained class must have a matching owned source file under `com.google.common` or `com.google.thirdparty.publicsuffix`. The latter is Guava's own Java implementation, despite its namespace name. Both endpoints of every analysis edge must be retained. This removes JDK references, external annotation libraries, failureaccess and genuinely external implementation types from all graph and UE counts.

Check `excluded_classes.csv`, `extraction_counts.csv`, and `class_aliases.csv` for a release. 'An external reference was observed in bytecode' is an audit count; it is not an edge in the cleaned analysis graph. The source JAR and binary JAR remain original input artifacts, while the analysis uses only their scoped contents.

## 8. What happens to Guava's @Beta classes?

An `@Beta` annotation describes the stability of an API. It does not turn a class into third-party code or make the containing stable release a beta release. We exclude prerelease **versions**, but retain source-owned production classes marked `@Beta`. This avoids changing the scope between release labels and API annotations.

## 9. What does an edge mean?

An edge `A -> B` means A depends on or uses B. A child points to its parent; an implementation points to its interface; a caller points to the symbolic target class emitted by the instructor extractor. The separate UE evidence may resolve that symbol to a declaring member; those supplementary edges do not silently augment the primary graph. All seven categories on tutorial slide 6 are retained and defined in `modeling_decisions.md`.

The typed CSV distinguishes categories. The graph used by ACDC and the lecture metrics is a binary directed union: repeated calls or multiple relation categories between the same ordered pair do not create extra edges. Otherwise a count of call sites divided by a maximum number of class pairs would not be a bounded density.

No self loops remain after class merging. The identity diagonal in k-means features is a modeling choice, not a genuine self-dependency included in MQ.

## 10. What information does static extraction miss?

It does not resolve arbitrary reflection or dynamic class names, execute service loading, or expand each virtual call to all possible runtime receivers. It cannot recover source dependencies erased by constant inlining. It uses base class entries of multi-release JARs to maintain a consistent implementation view.

These limits constrain the interpretation. They do not invalidate every static result, but they mean we cannot claim that the graph is the exact runtime call graph. The same extraction rules are applied to all versions.

## 11. Is your replacement really the original JNode algorithm?

No. The lecture discusses Constantinou et al.'s 2015 ComponentRank/shortest-path Noise method. The supplied 2020 paper proposes **usage equality (UE)** and compares it with JNode. The user requested a replacement based on that paper, so we implemented UE and call the tool **JNode-UE**. The report explicitly identifies the substitution.

This distinction is crucial in the oral exam. Do not describe UE as PageRank, a degree threshold alone, or a reimplementation of the supplied JAR. Its equations require member-level dedication evidence.

## 12. Explain the three UE equations

For a target class B, count each target member used by another retained class. Let `mx(B)` be the number of these distinct members. For a particular target member m, `xm_fanin(m)` is the number of distinct source members outside B that use m.

For caller class A, collect the **set** of B's target members used by any member of A. B's dedication to caller A is:

`D(A,B) = sum_m 1 / (xm_fanin(m) * mx(B))`.

Next compute `e(B) = 1 - max_A D(A,B)`. If one caller has a special relationship with B, the maximum dedication is larger and equality is lower.

Finally, `c(B) = 1 - 1/fanin(B)`, where this fan-in counts distinct caller **classes** in the member-use graph. B is removed only if both `e >= 0.85` and `c >= 0.90`. These example thresholds are empirical choices in the paper, frozen across the study; they are not mathematically optimal constants.

The word 'external' in the paper's member definition means outside B, within our scoped graph. It does not mean an external library should be counted.

## 13. Work through a simple UE example

Ten classes A0 through A9 each have one method calling a single method `Utility.log`. There are ten distinct source members and one referenced target member. For every A, dedication is `1/(10*1) = 0.1`. Therefore `e=0.9` and `c=1-1/10=0.9`: both inclusive thresholds pass.

Now give A0 a unique call to `Utility.setup`. The target has two referenced members. A0's dedication becomes `1/(10*2) + 1/(1*2) = 0.55`; equality becomes `0.45`. Cardinality remains `0.9`, but the utility is retained because A0 has a special relationship. This is the intended difference from merely removing high-degree classes.

## 14. Why do source members and caller classes differ?

Two methods in A calling the same B method contribute two source members to that target member's fan-in, but the target member is counted only once in A's target-member set. Repeating the same call instruction from the same source method does not add another source member.

After merging inner classes, keep distinct original member IDs. Otherwise two different methods with the same name and signature could collapse, changing the formula. The optimized implementation is tested against an independent exact-rational oracle.

## 15. What about classes with no member-use evidence or no detected noise?

Classes with no incoming retained method/field evidence receive a clear no-evidence decision and are retained. Inheritance-only or annotation-only references are not converted into fictional members. UE therefore answers a question about the documented member-use model.

Zero detections is a legitimate result for a release or a different system. A detector should not force a positive count by lowering a threshold after seeing the answer. All removals are simultaneous from the original graph; the algorithm does not repeatedly remove newly exposed candidates.

## 16. Why is the detector performant?

The implementation deduplicates and aggregates sparse member relationships with sets and dictionaries. It counts source members per target member, target members per class, caller-to-target-member combinations and caller-class dedication. It does not enumerate every possible subgraph or compute all-pairs shortest paths.

The main aggregation is linear in stored evidence, with deterministic sorting for output. Read the benchmark JSON for the measured hardware/runtime and sizes. Synthetic detector-only times and full Guava extraction-plus-detection times are different measurements and should not be conflated. We do not claim a measured speedup over the broken supplied tool because no valid matched baseline was established.

## 17. What does ACDC do?

The lecture describes pattern-based skeleton construction followed by orphan adoption. We use the official York Java implementation, preserve its source and archive hash, and run it on RSF dependencies. We do not replace it with a similarly named community-detection algorithm.

Our selected patterns are subgraph decomposition and orphan adoption (`+so`). The C body/header pairing pattern does not apply to a graph already merged to top-level Java types, so it is explicitly omitted. The pilot examines subgraph-size settings, and one configuration is fixed for all releases.

The size parameter does not promise every final cluster has at most that many nodes. Later orphan handling can produce a larger cluster. We report actual cluster-size distributions. Isolates absent from a dependency-only RSF file are explicitly restored as singleton clusters, with that wrapper behavior recorded.

## 18. How does k-means see a class?

A row describes the class's outgoing and incoming neighborhood. Columns have fixed class identities across the study. We add an identity entry, concatenate outgoing and incoming profiles, and normalize the row's length to one. K-means then minimizes within-cluster squared Euclidean distance between these vectors.

For a graph A -> B with union columns A,B,C, the outgoing part for A includes its identity A and target B; its incoming part includes identity A. This makes the representation concrete. Adding a class to a release changes rows and nonzero entries, not the definition of a feature.

In the filtered case, removed classes have no rows and their incident dependencies are absent from all remaining rows. Their coordinate positions may remain as zero columns, which do not influence Euclidean distances.

## 19. How did you choose k, and which parts were your own decisions?

We ran one preselected middle-release pilot with a declared candidate grid of k values and the same fixed feature representation. We selected the diminishing-returns elbow from normalized inertia: the candidate furthest from the straight line between the grid endpoints. The full candidate measurements and tie rule are saved. Inertia measures squared-distance fit, not architecture quality; the chosen elbow is not guaranteed to be unique or optimal.

Let the pilot have `n_p` classes and selected `k_p`. Every version uses `ceil(n_full*k_p/n_p)`, reusing its full-graph value after UE filtering and clamping only if fewer nodes remain. That extrapolation preserves an approximate target number of classes per cluster. The assignment asks us to explain k, but neither it nor the lecture requires this one-pilot strategy or scaling formula. Keeping the same seven dependency types is a separate choice about the input features. These are stated modeling decisions and still need interpretation alongside cluster sizes and MQ.

The sampling revision keeps that strategy. It changes the middle release to 25.0 and the set of class coordinates, so the pilot and final results are recalculated. The old 25.1 calibration is not automatically reused. It would be inaccurate to say that no parameter experiment was performed: there is one pilot sweep, followed by a fixed rule for the final runs.

The pilot is the only k sweep. Each final A3/A4 condition has one result under the frozen rule. The seed and ten internal initializations are fixed. A reviewer can also supply `--k` to the exploration command; those results belong in a separate directory, not mixed into the final series. Open `docs/pilot_decision.md` to quote the actual chosen pilot numbers.

## 20. Why four architectures if the note says one per version?

The assignment's table explicitly requires A1=ACDC/full, A2=ACDC/filtered, A3=k-means/full and A4=k-means/filtered. We interpret 'one analysis' as one finalized configuration/result per required condition after a pilot. There are 30 x 4 = 120 final algorithmic partitions, with no independent parameter sweep at each version.

## 21. Derive the lecture's quality measures

For cluster i containing `n_i` classes and `mu_i` directed internal edges, cohesion is `A_i=mu_i/[n_i(n_i-1)]`. A singleton has no possible nonself internal edge; we define its cohesion as zero and disclose that convention.

For two clusters i and j, let `epsilon_ij` count edges in both directions across their boundary. Coupling is `E_ij=epsilon_ij/(2*n_i*n_j)`.

MQ is the mean cluster cohesion minus the mean coupling over unordered cluster pairs:

`MQ = (sum_i A_i)/k - 2*sum_{i<j}E_ij/[k(k-1)]`.

For one cluster, the intercluster term is zero. The code validates complete one-to-one node coverage and a binary loop-free graph before applying these formulas. It does not silently mix this lecture MQ with the different cluster-factor MQ used in some Bunch literature.

## 22. Compute MQ by hand

Use nodes A,B,C,D with clusters {A,B} and {C,D}. Edges are A->B, B->A, C->D, D->C and B->C. Each cluster has 2 nodes and 2 directed internal edges, so each cohesion is `2/(2*1)=1`.

There is one cross-cluster edge and eight possible directed cross pairs, so coupling is `1/(2*2*2)=0.125`. MQ is `1-0.125=0.875`. There are 5 graph edges; four are internal. Show where each numerator came from before stating the final answer.

## 23. Why is MQ alone insufficient?

Different cluster granularity, singletons, graph sparsity and class removal affect the score. A very coarse partition removes many cross-cluster boundaries without necessarily producing useful modules. Macro averages also give small and large clusters equal weight.

Therefore we report cohesion and coupling separately, cluster sizes, singleton counts and edge retention. Supplemental weighted densities and agreement measures help interpret the output. No score substitutes for understanding whether a module has a coherent responsibility.

## 24. How do you compare full and filtered architectures fairly?

First show the direct A1/A2 and A3/A4 results with their node and edge counts. Then compare on the same retained graph: restrict the full partition to retained nodes and evaluate it on exactly the same nodes and edges as the newly recovered filtered partition. This separates the effect of changing membership from the fact that removal itself changes the graph.

This is an additional evaluation of existing partitions, not a new recovered architecture. Do not call a higher score after deleting dependencies proof that the original system's design improved. We did not modify Guava's source code.

## 25. What does architectural evolution mean in this study?

We inspect trends in class counts, edges, density, omnipresent counts, partition quality and changes on common nodes. We investigate discontinuities using release notes and source evidence. A spike can reflect an added subsystem, changed extraction-visible types or a reorganization; it is not automatically erosion.

Lehman's laws are empirical observations with qualifications, especially for E-type systems. More classes are compatible with growth but do not prove more functionality. Structural quality measures do not directly measure user satisfaction or organizational effort. A violation of intended architecture requires an intended rule and evidence of its violation.

## 26. What did the AI actually receive and produce?

Use the exact records in `results/ai/`: the supplied evidence, prompts, model/session description, complete class-to-module assignment, and evaluation. Distinguish the AI used to help prepare this project from the specific latest-release recovery experiment required by Phase 4.

AI can give semantic names and explain relationships from evidence. It can also over-rely on package names, overlook exceptions or produce plausible but unsupported structures. A valid partition must assign every scoped class exactly once and contain no external or invented classes. Inputs and prompt emphasis can change its partition; the report records the actual experiment rather than claiming unperformed trials.

## 27. Which method is best?

Answer in terms of measured properties and the intended use. ACDC seeks familiar structural patterns; k-means groups similarity profiles; AI may offer comprehensible semantic modules. A method that scores better on one structural metric in Guava is not automatically best for another system or for every architectural view.

Without an independently validated reference architecture, agreement with packages or another algorithm is not accuracy. We report MoJoFM as partition agreement in both directions. The absence of ground truth prevents calling these scores recovery accuracy; it does not prevent calculating agreement.

## 28. Can you reproduce everything?

Start from the README commands. Explain which steps require network access (fetching exact artifacts/tools) and which run locally from the recorded data. Show the frozen manifest/configuration, tool checksums, software versions, test results, run manifest and output validation.

If the examiner chooses a CSV cell, trace it back to a formula, partition, graph edge set and release artifact. If they choose a removed class, inspect its strongest caller and member counts. If they choose a graph jump, distinguish the measurement from your explanation and show the supporting source.

## 29. Why did you revise the annotation policy?

The original custom graph counted annotation applications as dependencies, making build/nullness marker types large hubs. UE depends on method/field member use, so it could not remove those hubs merely because many declarations carried an annotation. The revised primary graph is the instructor extractor's graph under documented normalization; supplemental annotation-application edges are not added. Every graph CSV identifies that source.

Owned annotation types still appear in the complete class inventory, including isolates. This means class counts, singleton counts and MQ can still be affected by metadata types. We report annotation and isolate breakdowns explicitly. We do not delete Guava classes merely because they have `@Beta`, and we do not assume every annotation is behaviorally irrelevant: Guava's EventBus reads `Subscribe` and `AllowConcurrentEvents` through ordinary class references.

## 30. What changed in the public-suffix decision?

The earlier namespace-only boundary treated `com.google.thirdparty.publicsuffix` as external. Its Java files carry Guava Authors headers and are distributed as part of the main implementation. The revision therefore includes those project-owned types. Names such as “thirdparty” are clues to inspect ownership, not a sufficient exclusion test. JDK and separately supplied libraries remain excluded.

This also improves interpretation of historical package moves: a type moving from `com.google.common.net` into Guava's public-suffix package remains within the owned scope. Its canonical name still changes, so a name-based churn metric may report removal/addition rather than recognizing a rename automatically.

## 31. What does MoJoFM mean, and why two directions?

MoJo compares partitions through element moves and cluster joins. MoJoFM normalizes the distance relative to the reference partition. Therefore reversing the inputs can change both the distance and its normalization. The recorded columns state which partition is source and which is target. The implementation convention for identical singleton/empty boundaries is documented and tested.

For filtering comparisons, first project the original partition to the retained classes. For temporal comparisons, use the common class identities. A MoJoFM agreement value between two algorithmic partitions is valid even without ground truth, but it should not be called accuracy. The measure ignores whether a module name is semantically meaningful; inspecting actual responsibilities remains necessary.

## 32. Do the revised results isolate the effect of each change?

No. The revised whole study changes the graph baseline, source scope, release sample and k calibration together. The original run is preserved for transparency, but its aggregate MQ differences cannot be attributed to one factor. Controlled checks on a shared version can isolate individual graph differences; the report labels those separately. Do not claim that a new higher MQ proves any one revision improved the architecture.

## Useful vocabulary

| English term | Greek term / meaning |
|---|---|
| Architecture recovery | Ανάκτηση αρχιτεκτονικής |
| Cohesion | Συνοχή |
| Coupling | Σύζευξη |
| Dependency | Εξάρτηση / συσχέτιση |
| Omnipresent class | Κλάση ευρείας χρήσης |
| Clustering / partition | Συσταδοποίηση / διάτμηση |
| Intended / implemented architecture | Προβλεπόμενη / υλοποιημένη αρχιτεκτονική |
| Reverse engineering | Αντίστροφη μηχανική |
| Orphan adoption | Υιοθεσία ορφανών |
| Threats to validity | Περιορισμοί στην εγκυρότητα των συμπερασμάτων |

The real examination preparation is to run the code and explain a concrete example together. Use `commit_roadmap.md` to divide verification work, and record only actual work in `contributions.md`.
