# Reproduce and audit the revised study

The revised experiment is defined by `config/versions.json`, `config/analysis.json`, the one-pilot calibration and the pinned original artifacts. Reproduction has three distinct levels: verify recorded evidence, recompute algorithmic outputs, and perform a genuinely new live AI recovery. These levels do not make the same reproducibility claim.

## 1. Prerequisites

Use Python 3.12 and Java 17+. The recorded run uses the exact Python packages in `requirements.lock.txt`. `EVOLUTION_JAVA` can point to a Java executable when the desired runtime is not on PATH. The repository includes a checksum-pinned Eclipse compiler, ASM, the original ACDC source archive and the instructor DependencyExtractor JAR with its unchanged bundled dependencies.

The instructor executable is launched through `CompCalc.MainClass` with an explicit classpath. This avoids its original jar-in-jar launch problem on the recorded Java runtime without modifying its algorithm. Neither Java analysis process executes target Guava classes. Analysis-tool libraries are not nodes in the target architecture graph.

```bash
git clone https://github.com/ckontz01/software-evolution-ex1.git
cd software-evolution-ex1
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
```

The package installation can require network access. Once the recorded artifacts/tool dependencies are restored, the data checks and computation use local files.

## 2. Verify the published data without recalculating architectures

```bash
python scripts/select_versions.py --check
python scripts/unpack_data.py
python scripts/fetch_tools.py
python scripts/fetch_data.py --offline --verify-git
python scripts/run_checks.py
python scripts/validate_results.py
python scripts/evaluate_ai.py
```

The selector reconstructs the exact 30-release sample from the frozen 45-family catalog: 24 major-version anchors, the latest endpoint and five optional minor releases chosen by the calendar-gap rule. It verifies the minimum spacing and per-major addition cap. It does not query new tags or inspect outcomes. The unpacker verifies archive and member hashes before restoration and refuses to overwrite differing local files. Offline acquisition verifies all 90 Maven artifacts and repeats the two endpoint Git/source checks.

The schema-3 archive manifest stores each version and pilot ZIP as a base64 `.zip.b64` text file, with separate byte counts and SHA-256 checksums for the stored text and decoded ZIP. `upstream_git.zip` remains a whole ZIP. `unpack_data.py` decodes the text automatically, verifies both representations and all member paths and hashes, then restores the normal directory hierarchy. No manual decoding is needed. The reader also accepts the earlier whole-ZIP and multipart formats. [Storage details](../archives/README.md)

The focused checks exercise real Java extraction/normalization, UE boundaries, ACDC and k-means adapters, pilot elbow rules, release selection, lecture metrics, MoJoFM and archive restoration. The independent result audit checks the saved population, instructor raw-to-normalized edge identity, source ownership, member/UE evidence, final partitions, quality terms, pilot selection, all comparisons and hashes. It is not a set of millions of unit tests: its total counts individual evidence assertions.

`evaluate_ai.py` verifies the recorded prompt/input hashes and complete saved partition, then computes the lecture metrics and both-direction MoJoFM on matching full and retained graphs. The AI response is the preserved experiment from the preceding instructor-extractor study; its latest-version graph inputs are unchanged. Only the derived comparisons against the current A1–A4 results are refreshed. This command does not call an AI model or recover another architecture.

## 3. Recompute the complete classical study

To avoid replacing the canonical restored outputs:

```bash
python scripts/run_study.py --phase all \
  --graph-root data/recomputed_graphs \
  --output results/rerun/recomputed
```

The pipeline prepares Java tools, performs supplemental ownership/member extraction, creates a deterministic instructor input JAR from unchanged owned base class bytes, runs the unmodified instructor tool, and normalizes its raw relationships. It retains source-owned common/publicsuffix types and isolates, removes external endpoints and merging-created self-loops, and preserves both typed evidence and a binary directed union.

The same sorted union coordinate system is used for all k-means runs. The middle selected release supplies one inertia grid; its chosen `k_p/n_p` calibration is reused by every final version. Each version generates exactly one A1, A2, A3 and A4 partition. The separate matched-k pilot diagnostic does not select the final k.

The command saves graph, input, algorithm-source and configuration hashes. In a compatible environment, deterministic graph/partition/metric outputs can be compared byte for byte. Runtime seconds, absolute paths and environment descriptions can legitimately differ and should not be treated as algorithmic mismatches. Fixed seeds do not promise cross-platform floating-point bit identity.

The default paths intentionally regenerate canonical `data/graphs` and `results` data. Use them only when replacing that recorded experiment is intended, then rebuild every dependent audit and report. The standalone independent validator targets canonical results.

## 4. Regenerate supporting analyses and the report

After restoring or recomputing canonical data:

```bash
python scripts/benchmark_ue.py
python scripts/audit_ue_cases.py
python scripts/audit_change_points.py
python scripts/audit_revision.py
python scripts/evaluate_ai.py
python scripts/validate_results.py
python scripts/build_report.py
```

These commands record performance, exact-fraction UE cases, all sampled graph transitions, controlled original/revised edge differences, AI scores and independent verification. They do not create new final A1-A4 architectures. Timed benchmarks naturally vary between executions.

The report generator reads saved measurements and validates their joins and hashes. It writes `report/guava_evolution_report_revised.pdf` and an identical canonical `report/guava_evolution_report.pdf`, plus PNG/SVG figures and `report/report_manifest.json`. The latter hashes its data inputs, source methods, documents and outputs. Missing required classical or actual AI evidence is an error; no placeholder result is substituted.

Use `python scripts/build_report.py --render-qa` if PyMuPDF is available to render every report page. Rendering/geometry checks support visual review but do not replace inspecting tables, formulas and figures.

## 5. Choose parameters for a separate exploratory result

```bash
python scripts/explore_release.py \
  --version 33.7.2 --k 40 --acdc-size 20 \
  --usage-threshold 0.85 --cardinality-threshold 0.90 \
  --output results/rerun/my_k40
```

The reviewer explicitly selects k here. The command uses the same extracted inputs and feature schema but stores the result separately from the final study. A new threshold changes which graph is retained; compare only matching populations when assessing its effects.

For detector-only use:

```bash
python scripts/jnode_ue.py \
  --classes data/graphs/33.7.2/classes.csv \
  --members data/graphs/33.7.2/member_dependencies.csv \
  --output results/rerun/ue_demo
```

## 6. Prepare evidence for a genuinely new AI experiment

```bash
python scripts/prepare_ai_inputs.py --output results/rerun/ai_new
```

This creates the class/edge files, package counts, package dependencies, matching source documentation, exact prompt and hash record for a new session. It refuses to overwrite an existing completed assignment. It does **not** fabricate or automatically obtain an AI response.

An actual independent model session must read the recorded prompt, write the initial names-only hypothesis before other evidence, then produce one complete final partition, architecture explanation and activity record. The allowed input set excludes ACDC/k-means results, UE decisions and quality metrics. The recorded canonical experiment followed that protocol; the coordinator evaluated afterward.

Recomputing the saved canonical AI scores is deterministic. Replaying a live model need not produce the same modules because the service exposes no full model-state/seed control and the model has general pretrained knowledge. A new response should preserve its own record rather than silently replacing the original experiment.

## 7. Read a verification record correctly

`results/validation.json` describes the current canonical independent audit. `results/reproducibility/` records the exact commit and environment tested by an independent checkout. Check its commit and configuration hashes before using it as evidence for a different revision. The original study is preserved at commit `d970305` and under `results/baseline_v1`. Any earlier checkout receipt applies to its recorded commit; a new report does not extend that receipt to the current study.

A byte-identical rerun establishes repeatability of the implemented method under the tested conditions. It does not prove completeness of static extraction, optimal k, correct semantic architecture or universal benefit from removing omnipresent classes.
