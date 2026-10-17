# Revised pilot decision: Guava 25.1

**Decision:** use the original ACDC implementation with `+so`, SubGraph size 20 and its default fine, flat output. For k-means, select **k=40** from the one-release inertia pilot, then freeze `ceil(n_full*40/554)` across the final study. A version's full and UE-filtered conditions reuse the same requested k, except a clamp if fewer nodes survive.

## Pilot input was selected before quality inspection

The pilot is **25.1**, index 16 of the 30 selected releases (zero-based index 15). Its instructor-derived internal graph has **554 canonical types and 2,681 directed edges**. All project-owned types are present, including isolates and the public-suffix implementation. The shared feature universe, identity terms, normalization and seed are the same as the final protocol.

ACDC is checked at size settings 10, 20 and 40. K-means is checked on the single declared grid below. This is the only k sweep: the final 30 versions do not each receive a search for favorable parameters. The grid and selection rule were frozen in `config/analysis.json` before the pilot, and the resulting calibration is pinned in `results/pilot/k_calibration.json`.

## Exact k-selection method

For every candidate k, record fitted inertia `I(k)` using the same sparse normalized features, `random_state=484`, `n_init=10`, Lloyd updates and the pinned numerical environment. Normalize:

```
x = (k - k_min) / (k_max - k_min)
y = (I(k) - I(k_max)) / (I(k_min) - I(k_max))
gap = 1 - x - y
```

Choose the interior candidate with maximum gap below the normalized endpoint chord; smaller k wins exact ties. If the maximum gap is below 0.02, or the curve is flat/nondecreasing, use the nearest tested candidate to the predeclared fallback k=30. No MQ value enters this decision. The raw curve is preserved without smoothing.

| Candidate k | Inertia | Normalized chord gap | Decision |
|---:|---:|---:|---|
| 2 | 510.124764 | 0.000000 |  |
| 5 | 489.042741 | 0.066670 |  |
| 10 | 465.722319 | 0.127282 |  |
| 15 | 449.478981 | 0.157646 |  |
| 20 | 438.058963 | 0.167394 |  |
| 25 | 426.446376 | 0.177965 |  |
| 30 | 415.554072 | 0.185458 |  |
| 40 | 396.560709 | 0.188513 | Selected |
| 50 | 380.055361 | 0.180934 |  |
| 60 | 365.947251 | 0.163109 |  |
| 75 | 342.956121 | 0.144189 |  |
| 90 | 322.556561 | 0.114192 |  |
| 110 | 298.564109 | 0.060489 |  |
| 130 | 276.159382 | 0.000000 |  |

The selected value is **40**, with gap **0.188513**. The fallback was not used, and there are no increasing-inertia steps in the observed curve. The calibration targets an average **554/40 = 13.85 classes per cluster**, extrapolated through `ceil(n_full*40/554)`.

The elbow is **broad**: k=30 has gap 0.185458 and k=50 has gap 0.180934. The deterministic maximum makes the decision reproducible, but this small separation does not establish a uniquely correct architectural granularity. The candidate range, graph and feature geometry influence the answer. The size-scaling rule is an explicit extrapolation assumption; it does not rerun the elbow calculation on every release.

## Observed pilot partitions and granularity diagnostic

| Method | Clusters | Largest | Singletons | Cohesion | Coupling | MQ |
|---|---:|---:|---:|---:|---:|---:|
| ACDC -l10 | 110 | 49 | 23 | 0.322771999 | 0.003494876 | 0.319277123 |
| ACDC -l20 | 110 | 49 | 23 | 0.322771999 | 0.003494876 | 0.319277123 |
| ACDC -l40 | 110 | 49 | 23 | 0.322771999 | 0.003494876 | 0.319277123 |
| KMeans elbow k=40 | 40 | 58 | 0 | 0.165473854 | 0.005165747 | 0.160308107 |
| KMeans matched ACDC k=110 | 110 | 23 | 9 | 0.246856351 | 0.004463248 | 0.242393103 |

The three ACDC assignment CSVs are byte-identical, with SHA-256:

`97a6039d957c004d38d6c0624a573b5750e448cd60d427cbc5c28564652a59ab`

This pilot gives no evidence that size 10 or 40 improves on 20. It does not show that the parameter is irrelevant on every graph. Later adoption can create a 49-class final group; `-l20` constrains a recovery stage, not every final cluster.

The **matched-k diagnostic** compares ACDC and k-means at 110 clusters on the same pilot graph. Raising k-means from its elbow-selected 40 clusters to 110 increases its MQ from 0.160308 to 0.242393; ACDC's MQ is 0.319277. This confirms that granularity affects the metric and explains part of the original gap on this pilot. A residual difference remains even at matched k, and matching k does not match the whole cluster-size distribution. The matched result was not used to select k and is not an additional official final architecture.

## ACDC representation fix carried into the revised study

The original file-oriented ACDC derives a basename by removing the last dotted suffix. Passing bare Java names `p.A` and `p.B` can therefore give both the basename `p`. The earlier adapter check identified this problem. The unchanged upstream tool now receives reversible `CLASS.java` IDs, yielding distinct basenames. `node_id_map.csv` records the mapping, and every membership is decoded to its canonical class name before evaluation.

A real-Java regression with two disconnected cliques in one package checks that their clusters remain distinct. Original ACDC source is unchanged; the wrapper also restores genuine graph isolates as singletons because dependency-only RSF cannot encode them.

## Evidence and reproduction

- `results/pilot/pilot.json`: actual pilot inputs, all final pilot metrics and matched-k diagnostic.
- `results/pilot/k_inertia_curve.csv`: candidate k, inertia, normalized coordinates/gap, iterations and runtime.
- `results/pilot/k_candidates/`: all 14 actual candidate assignments and fit metadata.
- `results/pilot/k_calibration.json`: selected value, explicit fallback logic, target mean, graph/class/feature/config/manifest hashes, and `quality_scores_used_for_selection=false`.
- `results/pilot/acdc_l10.csv`, `acdc_l20.csv`, `acdc_l40.csv`, `kmeans.csv`, and `kmeans_matched_acdc_k.csv`: actual memberships.

The frozen analysis configuration SHA-256 is:

`c2d715ba45c0ee9445e8d07bfba238c3a38d1dcf656aab909f828a7617ccb35f`

The matching calibration hash is included in `results/run_manifest.json`. The final study has exactly one A1/A2/A3/A4 partition per release under that calibration. User-selected `--k` runs use separate exploration directories. Tutorial pages 7–8 motivate checking original ACDC parameters; the reconstruction lecture pages 15–17 define the reported MQ. The inertia grid/elbow and size extrapolation are our declared implementation choices, not a lecture-prescribed theorem.
