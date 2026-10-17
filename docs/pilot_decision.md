# Pilot decision: Guava 25.0

The current cohort's middle release is **25.0**, the 16th observation (zero-based index 15). Its graph has **554 canonical types**. The previous 25.1 pilot belongs to the preceding cohort; it is not reused as this run's calibration. The feature and k-selection policies are unchanged, but their inputs are recomputed for the new sample.

## What the course requires and what this study chooses

The assignment asks how the number of groups was chosen (p.4). Lecture 6–7 slide 8 separates feature selection from the clustering algorithm. Neither specifies a single-release elbow or a size-extrapolation formula. This study uses one middle-release pilot, then applies one fixed rule to the final runs. The fixed seven dependency categories are a separate choice about the data representation.

## Exact k-selection rule

The pilot fits the candidates `2, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 110, 130` using the same normalized incoming/outgoing features, `random_state=484`, `n_init=10` and Lloyd updates. Inertia is the sum of squared distances to the fitted cluster centers. Normalize:

```text
x = (k - k_min) / (k_max - k_min)
y = (I(k) - I(k_max)) / (I(k_min) - I(k_max))
gap = 1 - x - y
```

Choose the interior candidate with the largest gap if it is at least **0.02**. Exact ties choose smaller k. If there is no usable interior candidate, the endpoint inertia drop is nonpositive, or the best gap is too small, choose the tested candidate nearest to the predeclared fallback **30**; ties again choose smaller k. The raw curve is not smoothed. Individual increasing-inertia steps are recorded, not automatically discarded or treated as a fallback trigger.

| k | Inertia | Normalized gap | Decision |
| --- | --- | --- | --- |
| 2 | 509.883145 | 0.000000 |  |
| 5 | 488.780931 | 0.066267 |  |
| 10 | 465.341761 | 0.126844 |  |
| 15 | 448.772054 | 0.158218 |  |
| 20 | 437.496292 | 0.167089 |  |
| 25 | 426.460345 | 0.174939 |  |
| 30 | 415.280126 | 0.183404 |  |
| 40 | 395.561358 | 0.189102 | Selected |
| 50 | 379.583274 | 0.178899 |  |
| 60 | 364.786559 | 0.163675 |  |
| 75 | 341.933385 | 0.143635 |  |
| 90 | 323.345275 | 0.105465 |  |
| 110 | 297.278265 | 0.060025 |  |
| 130 | 274.642098 | 0.000000 |  |

The selected value is **40**, with gap **0.189102**. The decision record is `maximum_normalized_chord_gap` and the observed curve has **0 increasing-inertia steps**. The candidate range, feature geometry and fitted optimization all influence the result. Nearby gaps should be inspected before describing the elbow as sharp or unique. This selection does not establish the number of true architectural modules.

## Applying the calibration

The pilot has **554/40 = 13.85 classes per cluster** on average. The final rule is `ceil(n_full*40/554)`. Each release's full and UE-filtered conditions request the same k, except that k is capped if fewer classes remain. An empty graph uses k=0. The final full-graph partitions contain **23–45 clusters**. Actual counts and warnings are saved for every fit.

Scaling by full class count is an explicit extrapolation assumption. No MQ value determines k, and final releases do not each receive another candidate sweep. An optional `--k` run belongs in a separate exploration directory.

## ACDC and the granularity comparison

| Method | Clusters | Largest | Singletons | Cohesion | Coupling | MQ |
| --- | --- | --- | --- | --- | --- | --- |
| ACDC -l10 | 110 | 49 | 23 | 0.323668029 | 0.003484828 | 0.320183201 |
| ACDC -l20 | 110 | 49 | 23 | 0.323668029 | 0.003484828 | 0.320183201 |
| ACDC -l40 | 110 | 49 | 23 | 0.323668029 | 0.003484828 | 0.320183201 |
| K-means selected k=40 | 40 | 69 | 0 | 0.164879222 | 0.005953027 | 0.158926195 |
| K-means matched k=110 | 110 | 28 | 4 | 0.268297258 | 0.004724264 | 0.263572994 |

The final ACDC configuration is the original York implementation with `+so -l20` and its default fine, flat output. The pilot checks sizes 10, 20 and 40; the table gives the measured differences. The size limit applies to the SubGraph stage, so later orphan adoption can create larger groups. A reversible `.java` suffix prevents the file-oriented tool from collapsing distinct Java names to the same basename. Genuine graph isolates are restored as singleton groups by the adapter.

The matched-k trial uses ACDC's cluster count to examine how granularity affects MQ on this one graph. It is a separate diagnostic and does not choose the final k. Equal cluster counts do not imply equal size distributions or meaningful responsibilities.

## Evidence

The full record is in `results/pilot/pilot.json`, `k_inertia_curve.csv`, `k_calibration.json` and `k_candidates/`. Each candidate has saved assignments and execution metadata. `quality_scores_used_for_selection=false` records the selection boundary. The final run pins the calibration hash.

Configuration SHA-256: `d13a902f38da8e0e921eec0d5ae152ea4a8cac84d8de91546240b865bf07c069`.

Calibration SHA-256: `61cf143f52f4b17f18f0c2470f25ad848872f008f3a99c82fa8698162777556c`.
