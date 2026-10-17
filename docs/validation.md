# Independent validation of the revised study

`scripts/validate_results.py` audits the saved evidence using only Python's standard library. It imports none of the production extractor, UE detector, clustering, metric, feature, k-selection, or MoJoFM functions. It does not create another architecture or rerun an optimization experiment.

Run the complete audit after unpacking the data and completing the AI evaluation:

```bash
python scripts/validate_results.py
```

The result is `results/validation.json`. A successful run exits with status zero and records `status: passed`, the evidence-check count, per-category counts, no failures, per-release measurements, and the checked AI population. These are **evidence checks**, not millions of independently designed unit tests.

For a deliberately limited audit during development, before the AI response is available:

```bash
python scripts/validate_results.py --skip-ai \
  --output results/rerun/core_validation.json
```

The output explicitly records that the AI experiment was excluded. A missing or malformed required artifact produces an incomplete result; a disagreement produces a failed result with the observed and expected evidence.

## What is independently checked

### Release selection and input provenance

The validator rebuilds the eligible family catalog from the frozen tag inventory. It checks the 30 distinct major/minor families, the family-rank selection, the declared boundary convention, and the stable-patch representatives. It checks dates, commit identities, JRE flavour, source prefixes, and checksums. The obsolete requirement to skip a release between every adjacent sample is not applied to the revised family-based selection.

For every release, it verifies the binary JAR, source JAR, and POM hashes. Every binary class is accounted for as either owned or excluded. The aliases must reconcile with the retained outer-type inventory and matching source files. Both `com.google.common` and the Guava-owned public-suffix implementation are in scope.

### The instructor is the primary relationship source

The exact supplied instructor JAR and its bundled libraries are checked against their recorded hashes. Each scoped `instructor_input.jar` must contain precisely the owned base-class entries, and **every retained class file must have exactly the same bytes as the original Maven artifact**. Input inventory hashes, entry sizes, fixed ZIP timestamps, and successful invocation records are checked.

The validator then reads `instructor_raw.csv` itself. It maps endpoints through the class aliases, discards out-of-scope endpoints and resulting self-loops, deduplicates typed relationships, and forms their unweighted directed union. That independently computed result must equal `dependencies_typed.csv`, `dependencies.csv`, and the RSF graph. The exclusion rows, occurrence counts, and normalization counts are reconciled too.

The supplemental graph is checked separately. Member evidence must be internal and supported by the supplemental field/method relationships, including declaration-resolved references that the instructor graph may represent differently. Supplemental edges are never required to appear in the primary graph. Annotation counts and extractor differences are recalculated from actual evidence; the validator does not impose a blanket claim that an instructor graph can never reference an annotation type.

### UE and lecture quality metrics

All UE decisions are independently recomputed with exact rational arithmetic. The audit preserves the distinction between calling classes and calling members, includes threshold equality, and verifies no-evidence retention. The filtered graph must be precisely the induced graph after the recorded simultaneous removals.

Every A1-A4 partition must assign all of its declared classes exactly once. Isolates and the ACDC input-ID mapping are checked. The current result directory must contain exactly the selected study's 120 finalized partitions, so stale partitions from an earlier sample are detected.

Cohesion, coupling, MQ, supplementary metrics, and every saved cluster/pair term are recomputed from edge contributions. The same-retained-graph MQ comparisons and temporal common-node measurements are recomputed independently. Runtime records must be finite and nonnegative; their presence does not establish a speedup over another implementation.

### Pilot calibration and fixed k policy

All predeclared pilot candidates preserve their assignments and fit metadata under `results/pilot/k_candidates/`. The validator reconstructs the normalized `[A+I,(A+I)^T]` features and recomputes each candidate's sum of squared distances through the centroid identity:

\[
\operatorname{SSE}=n-\sum_C\frac{\left\|\sum_{x\in C}x\right\|^2}{|C|}.
\]

It independently checks the recorded inertia curve, normalized chord gaps, tie/fallback policy, selected k, and matched-ACDC-k diagnostic. The diagnostic must be marked as excluded from k selection. Calibration hashes must match the pilot graph, classes, feature universe, configuration, and release manifest. Every final A3/A4 requested k must follow the calibrated integer-ceiling rule from the full class count, with only the declared remaining-population clamp.

This verifies the recorded objective values and selection rule. It does not prove that the elbow is an optimal or intended architectural cluster count, nor that Lloyd's algorithm found a global minimum.

### MoJoFM in both directions

All 178 main comparison rows and their detailed JSON terms are recomputed on their explicitly declared class universe. Forward and reverse distances have their own reference-specific normalizers.

The validator uses a generic unit-capacity residual-network maximum flow for the tied-overlap problem. For the maximum-distance denominator, it builds a target-size Ferrers graph and computes a matching, rather than reusing the production implementation's sorted-size recurrence. This separate implementation was also checked against exhaustive shortest paths over actual Move/Join operations for all 2,960 ordered partition pairs with zero through five nodes. The four lecture examples are checked within every full audit.

MoJoFM indicates agreement with the chosen reference. No reference partition is automatically treated as validated intended architecture. ARI remains an independently recomputed supplementary agreement measure.

### Recorded AI recovery

The default audit verifies the prompt and input hashes, confirms that the AI saw the same primary classes and dependencies, and independently reconstructs its package summaries and unmodified package-documentation input from the matching source archive. It checks the final partition's complete coverage, module counts, output hashes, full and retained lecture metrics, and both directions of all four AI/baseline comparisons.

Those checks establish that the saved record and arithmetic are consistent. They cannot inspect private model knowledge or independently prove its declarations about what it consulted. The AI receives semantic information that structural algorithms do not receive; the report retains that information-asymmetry limitation.

## What passing means

Passing establishes that the published measurements agree with the retained inputs and the declared revised protocol. It does not prove that a static extractor sees reflection or every dynamic dispatch target, that a high MQ identifies the intended architecture, or that every reasonable graph or sampling policy would produce the same scientific interpretation. The tests, independent audit, source-based interpretation, and explicit modeling choices address different questions and are all needed for a defensible oral explanation.
