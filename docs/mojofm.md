# MoJoFM: agreement with an explicit reference partition

MoJoFM supplements the required cohesion, coupling, and MQ evaluation with the partition-comparison method in **Lecture 6-7, pages 28-32**. It asks how many elementary changes are required to turn a source partition into a chosen target partition. It uses class membership, not dependency-edge density.

In this study, a reference may be a named package partition, another algorithm's partition, or a partition from another sampled release after projection onto common classes. These are comparison references. Their availability does not establish that they are independently validated intended architectures. We therefore describe the results as **partition agreement**, not architectural recovery accuracy.

## Definition and direction

A **Move** transfers one class into another cluster, including a newly created cluster. A **Join** merges two whole clusters. Each costs one operation. Empty clusters disappear, and cluster names have no effect.

For source partition A and target partition B:

\[
\operatorname{MoJoFM}(A,B)=100\left(1-
\frac{\operatorname{mno}(A,B)}{\max_X\operatorname{mno}(X,B)}\right).
\]

The numerator is the minimum number of operations **from A to B**. The denominator is the greatest distance **to that same B** among all partitions X of the same classes. The production function preserves this direction; it does not take the smaller distance of the two directions. The exact algorithms follow Wen and Tzerpos [1], sections 3-4.

For example, transforming `{a,b,c,d}` into `{a,b}, {c,d}` requires two Moves. Reversing that transformation requires one Join. The respective target normalizers are 2 and 3, giving 0% and 66.67%. Reporting an unlabeled average of the directions would obscure the question being asked.

## Exact calculation

Let \(v_{ij}=|A_i\cap B_j|\). Each source cluster can retain its largest overlap with a target cluster, while its other members move. Ties require care: choosing an arbitrary tied target can cause an unnecessary Join.

The implementation builds a bipartite graph linking each source cluster only to targets attaining its row's maximum overlap. A maximum-cardinality matching gives \(g\), the largest number of target groups that can remain occupied by distinct source clusters. Iterative augmenting paths resolve ties exactly. The distance is:

\[
M=n-\sum_i\max_j v_{ij},\quad
J=|A|-g,\quad
\operatorname{mno}(A,B)=M+J.
\]

The reported M and J describe one optimal construction. Another shortest sequence may exchange a Join of a singleton for a Move without changing the total.

### Why greedy tie handling is wrong

Take source `{a,b}, {c}` and target `{a,c}, {b}`. The first source cluster overlaps both targets by one class; the second overlaps only the first target. Assigning both source clusters to the first target produces one Move plus one Join. A matching assigns the first source cluster to the second target and the second source cluster to the first target. Moving `a` into `{c}` completes the transformation in **one** operation.

### The normalizer is target-specific

Sort the target cluster sizes in ascending order. Start G at zero; increment G for a size only if that size is greater than the current G. Then:

\[
\max_X\operatorname{mno}(X,B)=n-G.
\]

The lecture's eight-node example has target sizes 2, 3, 3. The recurrence gives G=3, hence its denominator 8-3=5. **The denominator is not generally n minus the number of target clusters.** For target sizes 1, 1, 3, G=2 and the correct denominator is 5-2=3, although there are three target clusters. An explicit farthest source is `{a,b,c}, {d}, {e}` for target `{a}, {b}, {c,d,e}`.

## Coverage, empty cases, and comparability

- Both inputs must assign every class exactly once on the **same universe**. Different universes are rejected. Any projection belongs to the calling analysis and must be reported along with its common/retained class count.
- Only nonempty clusters occur in the membership representation. A cluster containing one class is valid.
- For two or more classes, identical partitions score 100%; a partition at the target's maximum distance scores 0%.
- A zero-class or one-class universe has only one possible partition. Its distance and target maximum are both zero. We record `score: null`, `defined: false`, and the reason `empty_universe` or `single_node_universe`. We do not silently convert the undefined 0/0 normalization into an empirical 100% observation.
- Higher MoJoFM means fewer required transformations relative to the chosen target's maximum. It does not measure cohesion or prove architectural correctness.
- Changing the target changes the normalizer. Results with different targets or different common-class populations should be interpreted with their raw distance, class count, and target cluster count. Cross-version changes are descriptive; they are not controlled comparisons against one invariant reference.

For filtered/full comparisons, project the full-graph assignment onto the retained classes before comparing it with the filtered-graph assignment. For adjacent sampled releases, project both assignments onto their intersection. Give each direction an explicit name such as `previous_to_current` or `filtered_to_full_projected`.

## API and reproduction

The implementation is `src/evolution/mojofm.py` and depends only on the Python standard library:

```python
from evolution.mojofm import compare_mojofm, mojo_distance, mojo_max_distance

source = {"a": "one", "b": "one", "c": "two"}
target = {"a": "left", "b": "right", "c": "left"}
result = compare_mojofm(source, target)
assert result["distance"] == 1
```

`compare_mojofm` returns `distance`, `max_distance`, `score`, `defined`, `reason`, the explicit `direction`, the class/cluster counts, and the Move/Join/matching/normalizer terms. `mojo_distance` returns the directional integer distance alone; `mojo_max_distance` returns the exact normalizer for a target alone. Node and cluster identifiers must be nonempty strings.

Sparse intersection counts take one pass over the nodes. If s and t are the source and target cluster counts and E is the number of tied-maximum edges, the matching phase costs O(s(E+s+t)) in the worst case; E is at most the number of nonzero intersections, which is no greater than the number of classes. Sorting target sizes costs O(t log t). This is practical for the study's hundreds of classes and tens to hundreds of clusters. No enumeration of all possible partitions occurs during study execution.

## Independent correctness evidence

Run the focused tests from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_mojofm.py -v
```

The tests check the four lecture diagrams: distances **5, 0, 2, 3**, normalizer **5**, and scores **0%, 100%, 60%, 40%**. They also check the sixteen-object worked example from [1], direction, target normalization, label invariance, missing classes, and degenerate cases.

The strongest independent check enumerates **all 2,960 ordered partition pairs across n=0 through n=5**. It builds every actual Move/Join transition and finds minimum costs by breadth-first search. This oracle does not use overlap maxima, bipartite matching, or the normalization recurrence. The maximum of its observed distances to each target independently verifies the production denominator as well as the numerator. No equivalence to an unexecuted third-party program is claimed.

## Sources

1. Zhihua Wen and Vassilios Tzerpos. **An Effectiveness Measure for Software Clustering Algorithms.** Proceedings of the 12th IEEE International Workshop on Program Comprehension, 2004, pp. 194-203. [Author-hosted paper](https://www.eecs.yorku.ca/~bil/publications/mojofm.pdf); [author's publication record](https://bil.eecs.yorku.ca/publications/). Sections 3-4 provide the exact transformation and maximum-distance algorithms.
2. Supplied **Lecture6-7-ArchitectureReconstruction.pdf**, pages 28-32. The directional comparison and worked eight-class examples are the course basis for reporting this metric.
