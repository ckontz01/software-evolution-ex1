# JNode-UE: paper, implementation, and oral-exam explanation

## What was replaced

The supplied JNode was reported as incorrect, and the user requested a replacement based on **Yano and Matsuo, “Moderate Detection and Removal of Omnipresent Modules in Software Clustering,” ICSME 2020, pp. 662–666, DOI [10.1109/ICSME46990.2020.00068](https://doi.org/10.1109/ICSME46990.2020.00068)**. The replacement is called **JNode-UE** to make that substitution explicit.

The paper calls its proposed detector **usage equality (UE)**. Its JNode comparison is an earlier, different algorithm: Constantinou, Kakarontzas and Stamelos, “An automated approach for noise identification to assist software architecture recovery techniques,” *Journal of Systems and Software*, 107 (2015), 142–157, DOI [10.1016/j.jss.2015.05.065](https://doi.org/10.1016/j.jss.2015.05.065). That algorithm combines ComponentRank with shortest-path evidence. We do not claim that the replacement reproduces that historical JNode algorithm, and the experiment must label its noise filter as UE. This distinction matters when explaining the departure from the original tutorial tool.

UE detects classes before clustering. It does not decide the number of clusters and is not SArF clustering. It can provide the filtered graph to the ACDC and k-means experiments.

## Exact equations

The following definitions are from the attached paper, printed p. 663, equations 1–3 (PDF p. 2).

For a caller class A and target class B:

- **M_AB** is the set of members of B used by any member of A. Members include methods and fields.
- **xm_fanin(m)** is the number of distinct source members outside B that depend on the target member m.
- **mx(B)** is the number of members of B used by outside members. Unreferenced members do not enter this denominator.
- **fanin(B)** is the number of distinct caller classes of B.

The dedication of B to A is:

\[
D_M(A,B)=\sum_{m\in M_{AB}}\frac{1}{\mathrm{xm}_{fanin}(m)\,\mathrm{mx}(B)}.
\]

Usage equality and cardinality are:

\[
e(B)=1-\max_A D_M(A,B),\qquad
c(B)=1-\frac{1}{\mathrm{fanin}(B)}.
\]

The detector removes B only when both conditions hold:

\[
e(B)\geq 0.85\quad\text{and}\quad c(B)\geq 0.90.
\]

These thresholds are the paper's empirical examples, selected by experience. The paper does not prove that they are optimal. We keep the chosen thresholds constant across releases; the detector does not adapt them to obtain more attractive MQ scores.

The cardinality condition requires **at least ten distinct caller classes**. Nine callers give c = 8/9, below 0.90. Ten give c = 0.90 and satisfy the inclusive boundary. The implementation compares the integer count against the exact decimal threshold, avoiding the binary floating-point mistake in `ceil(1/(1-.9))`, which can return eleven.

## Why both conditions are needed

A utility with one operation called in the same way by ten classes has dedication 0.1 for each caller, e = 0.9, and c = 0.9. UE removes it.

A popular class may have a special caller. Suppose twenty ordinary classes and Startup use Logger.log, while Startup alone also uses Logger.init. There are two externally used members. Startup has dedication 1/(21 × 2) + 1/(1 × 2), approximately 0.524. Usage equality is approximately 0.476, so Logger stays even though it has twenty-one callers. Startup's exclusive use of init supplies evidence of a meaningful architectural relationship. This reproduces the reasoning of Figure 1, printed p. 663.

The paper's real examples, printed p. 664, illustrate the same distinction. Its model class has 82 callers but a maximum dedication of 0.151, giving e = 0.849, and is retained. Its StreamCloser utility has 11 callers, maximum dedication 0.112, e = 0.888, and c approximately 0.909, and is removed. Those are examples reported by the authors, not measurements of Guava.

## The two levels of deduplication

This is the most important implementation detail to defend in the oral exam.

Suppose A.first and A.second both access B.value, and C.run also accesses B.value. Then xm_fanin(B.value) = 3 because there are three distinct source members. There are only two caller classes. B.value appears once in M_AB even though A has two methods that access it. With one referenced B member, both D_M(A,B) and D_M(C,B) equal 1/3.

Counting caller classes instead of source members in xm_fanin would produce 1/2. Summing the same target member twice for A would produce 2/3. Both differ from equation 1. Repeating an identical call instruction several times inside A.first does not create a new source member and must not increase the count.

The code therefore deduplicates **source-member/target-member pairs** first, then separately deduplicates **caller-class/target-member pairs**. Method IDs include the original declaring owner, member kind, name, and descriptor so overloads, fields, and methods of different inner classes remain distinct.

## Project scope and extraction conventions

The paper defines the metric but does not specify every Java bytecode extraction decision. The following conventions implement the assignment's additional instructions and are explicit limits of the experiment.

1. The extractor identifies project classes from the selected Guava artifact and approved namespace. External JDK and third-party library classes are outside the analysis graph.
2. Genuine inner and anonymous classes are assigned to their outermost project owner using class metadata. The member ID still records the original declaring class. Class aggregation must not collapse distinct inner methods with the same name.
3. A dependency whose owners become equal after aggregation is internal to that single analysis class. It does not count as an incoming dependency from outside B.
4. The UE input contains resolved method-call and field-access member edges. The wider clustering graph may additionally contain the separately documented class relationship categories. Inheritance, annotations, or type mentions do not become artificial members just to force them into equation 1.
5. Consequently, UE fanin is the number of distinct callers in the **resolved member-use graph**. It is not automatically identical to the incoming degree in the wider class relationship graph. This is a stated extraction convention; the paper does not prescribe a mapping of every type-only Java relation to member evidence.
6. “External members” in the paper means members outside the target class B. It does **not** mean members of external libraries. Only in-scope project callers enter the computation.
7. Classes with no incoming resolved member-use evidence are retained. Their e and c are recorded as null because the paper's `max(empty)` and `1/0` are undefined. Null is not evidence of high usage equality.

Bytecode static analysis cannot recover all runtime behavior, including arbitrary reflection and dependency injection. The formula implementation is exact over its extracted input graph; that does not make the graph a complete runtime trace. Missing member resolution and filtered dependencies should be reported with the extraction diagnostics.

## One simultaneous pass

The paper's overall procedure, printed p. 664, is: construct the dependency graph, compute dedication, classify omnipresent modules using usage equality and cardinality, and cluster the graph after removing those modules.

JNode-UE computes every decision on the same original scoped graph, then returns the whole removal set. It does not remove one class, recompute the scores, and repeat. Such a cascade could change later decisions and is not the described method. For the same reason, there is no PageRank, shortest-path search, recursion, or convergence loop in this replacement.

## Implementation and result interface

Implementation: `src/evolution/omnipresent.py`. Tests: `tests/test_omnipresent.py`.

```python
from evolution.omnipresent import detect_omnipresent

result = detect_omnipresent(
    classes,
    member_rows,  # source_class/source_member/target_class/target_member
    usage_threshold=0.85,
    cardinality_threshold=0.90,
)
removed = set(result.removed_classes)
decisions = result.by_class()
json_ready = result.to_dict(include_dedications=True)
```

The alternative input form is an iterable of `(source_member, target_member)` tuples together with a `member_owners` mapping. Every member identifier must be globally unique and every owner must be a normalized class. Missing owners and conflicting assignments raise errors instead of silently losing evidence.

Each class decision records fanin, mx, maximum dedication, e, c, the strongest caller, the two threshold decisions, and a reason. The optional pair table records each D_M(A,B). Aggregate counters reconcile all input rows into excluded external edges, excluded intraclass edges, duplicate edges, and unique member edges.

The numerical computation uses accurately summed positive floating-point terms. When a dedication falls at the threshold's rounding boundary, the decision uses exact rational arithmetic. This preserves the inclusive mathematical rule rather than expanding it with an arbitrary epsilon.

## Performance and measured benchmark

The detector uses hash-based incidence sets and dictionaries. With R distinct member references, C class pairs, and N classes, its main aggregation takes expected O(R + C + N) time and O(R + C + N) space. Stable output sorting adds O(C log C + N log N). Exact rational arithmetic is used only for decisions at a floating-point boundary. It does not build an N × N dense matrix or enumerate all paths.

The following synthetic benchmark was run on 17 October 2026 with Python 3.12.14 on Linux x86-64. Each class calls twenty other classes in a ring, producing exactly twenty incoming caller classes per target. Every target has e = c = 0.95, and the benchmark checks those expected values. The cases measure scaling and do not represent application architecture quality.

| Classes | Distinct member references | Class pairs | Detector time, median of 3 runs | Process high-water RSS |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 20,000 | 20,000 | 0.087523 s | 33.99 MiB |
| 5,000 | 100,000 | 100,000 | 0.567056 s | 117.66 MiB |
| 10,000 | 200,000 | 200,000 | 1.236035 s | 221.87 MiB |

Timing covers the detector, including its validation, diagnostics, and sorting; it excludes input creation. RSS includes the input, result objects, and Python process, and is a cumulative high-water measurement across the three benchmark cases, not an isolated allocation measurement. These numbers are measured on this environment, not guaranteed times for other computers. They also do not include downloading or extracting a release or running clustering.

The full runs, environment, expected-output checks, protocol, and code hashes are saved in [ue_benchmark.json](../results/performance/ue_benchmark.json). Recreate that file with `python scripts/benchmark_ue.py`. The benchmark's original construction is also shown explicitly below and can be run from the repository root:

```bash
PYTHONPATH=src python - <<'PY'
import gc, json, resource, statistics, time
from evolution.omnipresent import detect_omnipresent
for n in (1000, 5000, 10000):
    classes = [f'C{i:05d}' for i in range(n)]
    owners = {f'{c}#run()V': c for c in classes}
    owners.update({f'{c}#accept()V': c for c in classes})
    edges = [(f'{classes[i]}#run()V', f'{classes[(i+j)%n]}#accept()V')
             for i in range(n) for j in range(1, 21)]
    times = []
    for _ in range(3):
        gc.collect()
        start = time.perf_counter()
        result = detect_omnipresent(classes, edges, member_owners=owners)
        times.append(time.perf_counter() - start)
        assert result.stats.unique_member_edges == n * 20
        assert len(result.removed_classes) == n
        assert all(s.fanin == 20 and abs(s.usage_equality - .95) < 1e-14
                   for s in result.scores)
    print(json.dumps({'classes': n, 'member_edges': len(edges),
        'median_seconds': statistics.median(times),
        'process_peak_rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}))
    del result, classes, owners, edges
PY
```

## Verification

Thirteen unit tests passed, including an independent, deliberately slow implementation of equations 1–3 using exact fractions on twelve seeded small graphs. Additional tests cover the ten-caller boundary, e = 0.85 exactly, field references, duplicate call sites, distinct source members within one caller class, rare setup methods, external-library exclusion, merged inner owners, unreferenced target members, simultaneous removal, invalid ownership, isolated classes, and deterministic JSON-safe output.

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_omnipresent.py -v
```

The independent oracle checks the mathematics. The extractor's separate integration fixtures check whether Java bytecode is converted to that evidence correctly. Both are needed: correct equations alone cannot repair a bad dependency graph.

## Extractor audit and integration evidence

Eight integration tests in `tests/test_extractor.py` also passed. They compile a small Java fixture with ECJ, construct binary and source JARs, run the real ASM extractor, read its CSV files, and feed its member rows directly to UE. The application classes are never executed. The fixture includes a class whose initializer would throw if executed.

The audit corrected two problems that a plain class-count check would miss. First, nested generic type arguments need their own signature visitors: the signature `Outer<Arg>.Inner<Result>` names `Outer$Inner`, and visiting Arg must not replace the enclosing owner. The fixture deliberately includes a real top-level class named `Arg$Inner` (using its fixture-specific name), so an incorrect visitor would emit a detectable, spurious dependency. Second, field and method declaration lookup require different orders. Field lookup checks the owner, then its interfaces recursively, then its superclass; class method lookup searches the superclass chain before interface methods and selects the unique maximally-specific concrete interface method when one exists. The basis is [JVMS 5.4.3.2–5.4.3.4](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html). Successful lookups and unresolved lookups are both cached.

Some eligible interface declarations can remain tied; the JVM specification permits an arbitrary resolution choice in that case. The extractor chooses lexically to make repeated extraction deterministic and records `interface_resolution_ties`. It does not expand calls to all possible dynamic receiver implementations. Declaration lookup uses the metadata available in the artifact, so unavailable library ancestors limit resolution coverage; this is not a complete JVM linker. Unknown target declarations supply no UE member edge. Their original symbolic class relation is retained only when its endpoint is an owned project class, and the unresolved member use is recorded separately.

The integration fixture verifies all seven typed relations, inherited declaring owners, the interface-field ordering case, the more-specific default-method case, anonymous and inner owner merging with distinct original member IDs, legitimate top-level dollar names, namespace/source-ownership filtering, multi-release entry exclusion, and identical CSV bytes from repeated runs. It verifies the following emitted relation vocabulary:

| Relation | Bytecode evidence |
| --- | --- |
| `EXTENDS` | A class superclass or an interface superinterface |
| `IMPLEMENTS` | An implemented interface of a class |
| `METHOD_CALL` | A method/constructor instruction or relevant method handle |
| `FIELD_REFERENCE` | A field access instruction or relevant field handle |
| `METHOD_PARAMETER` | Reference types in method parameter descriptors |
| `EXCEPTION_THROWS` | Declared method exception types |
| `TYPE_USAGE` | Other reference-type evidence such as return/field types, generic signatures, casts, annotations, arrays, class literals, and catch types |

Only owned, distinct normalized class endpoints appear in these outputs. Compile-time synthetic methods and initialization methods are bytecode members; their original identifiers are retained. Counts therefore describe the shipped artifact under these stated rules, rather than every source-level or runtime relationship.

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_extractor.py -v
```
