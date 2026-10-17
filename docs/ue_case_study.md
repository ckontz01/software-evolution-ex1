# Two independently checked UE decisions in Guava 33.7.2

The checks below reconstruct the paper's mathematical sets directly from the extracted member CSV and use exact rational arithmetic. The audit script does not import the production detector. It checks every caller's dedication before choosing the maximum, then compares both decisions with the finalized `ue.json` output.

Release: `v33.7.2`; commit: `666338cc49d5686c07e3e4d17f0aa1cec25a2be6`. The graph has 591 normalized project classes and 9,472 distinct member edges. UE removes 22 classes under the fixed e ≥ 0.85 and c ≥ 0.90 rule. These are preprocessing decisions; no extra architecture was generated for this audit.

Complete numerical evidence, exact fractions, CSV row references, all caller scores, and input SHA-256 values are recorded in [case_checks.json](../results/performance/case_checks.json). The primary inputs are [member_dependencies.csv](../data/graphs/33.7.2/member_dependencies.csv) and [ue.json](../results/versions/33.7.2/ue.json). The method follows [Yano and Matsuo, 2020, equations 1–3, p. 663](https://doi.org/10.1109/ICSME46990.2020.00068).

| Target | Distinct caller classes | Referenced target members | Maximum dedication | Usage equality | Cardinality | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `com.google.common.base.Preconditions` | 312 | 29 | 0.072372307325 | 0.927627692675 | 0.996794871795 | Remove |
| `com.google.common.collect.Iterators` | 50 | 41 | 0.501964769648 | 0.498035230352 | 0.980000000000 | Retain |

## Removed: Preconditions

The strongest caller is `com.google.common.io.BaseEncoding`. It uses 8 of the 29 externally referenced members of Preconditions. Across the system, the incoming evidence contains 1,643 distinct member edges from 312 caller classes. Those quantities are different: xm_fanin counts distinct source methods or fields, while cardinality counts classes.

The 8 terms for the strongest caller are shown below. Each overload is a separate target member; JVM descriptors distinguish primitive and reference parameter types. For readability, the class prefix is omitted.

| Referenced Preconditions member | Distinct source members using it | Contribution to dedication |
| --- | ---: | ---: |
| `M:checkArgument(Z)V` | 98 | 1/2842 |
| `M:checkArgument(ZLjava/lang/String;C)V` | 1 | 1/29 |
| `M:checkArgument(ZLjava/lang/String;I)V` | 39 | 1/1131 |
| `M:checkArgument(ZLjava/lang/String;Ljava/lang/Object;)V` | 57 | 1/1653 |
| `M:checkNotNull(Ljava/lang/Object;)Ljava/lang/Object;` | 980 | 1/28420 |
| `M:checkPositionIndexes(III)V` | 71 | 1/2059 |
| `M:checkState(ZLjava/lang/Object;)V` | 33 | 1/957 |
| `M:checkState(ZLjava/lang/String;CC)V` | 1 | 1/29 |

Adding these exact fractions gives **1190325491/16447250820 ≈ 0.072372307325**. All 312 caller scores were checked; none is larger. Therefore e = 0.927627692675 and c = 1 − 1/312 = 0.996794871795. Both thresholds pass, so UE removes Preconditions.

Even its strongest caller has a small share of the class's dedication. Its argument and state validation functions are broadly shared in this member-use graph. The conclusion comes from the measured calls and counts, not from matching the class name to a utility-name list. The matching source JAR confirms the `checkArgument` and `checkState` declarations; their entry hashes and line references are in the evidence JSON.

## Retained despite many callers: Iterators

Iterators has 50 caller classes, so its cardinality 0.980000000000 passes. Its strongest caller is `com.google.common.collect.Iterables`, which uses 31 of its 41 externally referenced members. Many of those operations are used by only one source member in the scoped graph.

The complete member list is in the JSON. Grouping equal denominators makes the manual calculation shorter:

| xm_fanin of a referenced target member | Number of such members used by Iterables | Combined contribution |
| ---: | ---: | ---: |
| 1 | 17 | 17/(1 × 41) |
| 2 | 3 | 3/(2 × 41) |
| 3 | 3 | 3/(3 × 41) |
| 5 | 2 | 2/(5 × 41) |
| 6 | 1 | 1/(6 × 41) |
| 8 | 1 | 1/(8 × 41) |
| 9 | 2 | 2/(9 × 41) |
| 10 | 1 | 1/(10 × 41) |
| 15 | 1 | 1/(15 × 41) |

Their sum is **7409/14760 ≈ 0.501964769648**. Consequently e = 0.498035230352, below 0.85, so Iterators is retained. The paired Iterables/Iterators usage supplies the specialization evidence. UE can preserve a class that offers utility operations when a particular caller has a strong relationship with it.

The matching source JAR also confirms that `Iterables.all`, `Iterables.any`, and `Iterables.find` delegate to their corresponding Iterators operations. These are concrete examples of the wider specialization pattern measured above; the source entry hash and exact lines are recorded in the JSON.

This case also explains why a large incoming degree alone is insufficient: both targets have many caller classes, but their maximum dedication scores differ substantially.

## What the decisions do not establish

The same finalized removal set includes `ImmutableList`, `ImmutableMap`, and `ImmutableCollection`. These are important collection API types. The moderate detector does not guarantee preservation of every important class, and a removal decision does not mean the class is unnecessary or badly designed. Guava itself is a library; useful shared functionality and architectural features overlap. No threshold was adjusted after observing these examples. Architectural quality must also be discussed through the requested clustering/evolution metrics and interpretation, rather than treating UE labels as ground truth.

## Quantified extraction limitations

The latest extractor records **657 unresolved member-use events**, representing **492 distinct recorded references**. After mapping source and target owners through the class aliases, **333 events / 266 distinct references** cross normalized class boundaries. The remaining recorded events are intraclass after merging.

There are 53,334 observed member-use events overall, so unresolved rows account for 1.232% of that raw event count. This denominator includes external and intraclass events. The percentage is therefore **not** a graph-completeness or false-negative rate. Missing library-ancestor declarations are a known boundary of artifact-only resolution, and the detector does not fabricate them as project members.

| Frequently unresolved signature | Recorded event rows |
| --- | ---: |
| `size()I` | 112 |
| `unlock()V` | 98 |
| `get(I)Ljava/lang/Object;` | 77 |
| `isEmpty()Z` | 48 |
| `ordinal()I` | 40 |
| `toString()Ljava/lang/String;` | 27 |
| `lock()V` | 23 |
| `getKey()Ljava/lang/Object;` | 22 |

There were 12 interface-resolution ties, resolved deterministically as documented in [omnipresent.md](omnipresent.md). Cached lookups recorded 39,788 hits across 13,546 distinct queries. Full unresolved evidence is retained in [unresolved_member_uses.csv](../data/graphs/33.7.2/unresolved_member_uses.csv); all emitted graph endpoints remain owned project classes.

## Reproduce the independent check

```bash
python scripts/audit_ue_cases.py --version 33.7.2
```

The script requires the finalized extraction and UE output. It verifies the fixed thresholds and decisions, saves all exact contributions and source-row evidence, and recreates this explanation. Detector performance can be reproduced separately with `python scripts/benchmark_ue.py`.
