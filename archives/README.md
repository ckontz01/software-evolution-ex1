# Complete revised study data

The current bundles preserve all **90 original Maven artifacts** for the 30 selected families, two immutable endpoint Git source archives, and complete detailed graph/algorithm evidence. The archive manifest is authoritative for the current member counts and hashes. Original-study data remain recoverable from the original Git commit; unselected old releases are not extra observations in this revised series.

Each release bundle includes the complete original binary JAR, matching source JAR and POM; the source-owned class inventory and enclosing aliases; the deterministic instructor input JAR and per-class original-byte hashes; the unmodified instructor tool's raw CSV, command and log; normalized primary typed/binary relationships; separate supplemental graphs and member references; exclusions and unresolved evidence; UE scores and retained graph; all A1-A4 partitions, metric terms, ACDC inputs/outputs/logs, and directional MoJoFM comparison details.

The pilot bundle preserves all three ACDC trials, all 14 k-means inertia-grid candidate assignments and run records, the selected pilot partition, matched-ACDC-k diagnostic and frozen calibration. It is separate from the 120 final architectures. Endpoint Git archives support offline repetition of the oldest/latest source-JAR comparison.

Restore from the repository root:

```bash
python scripts/unpack_data.py
```

This checks each archive and member SHA-256 before restoring `data/raw`, `data/graphs`, `data/upstream_git`, `results/versions` and `results/pilot`. Existing matching files remain; a differing local file causes an error. Use `--version 33.7.2` to restore one release, or `--verify-only` to audit stored bytes without writing.

`manifest.json` lists every original member and its digest. Fixed ZIP timestamps and sorted paths allow `python scripts/package_data.py` to recreate deterministic bundles from unchanged input files. It writes a temporary archive before replacing the prior one, so an interrupted packaging run does not erase a valid existing bundle.

The source code, summary tables, figures, configurations, acquisition provenance, report and documentation remain ordinary repository files. The fresh AI prompt/input/output and evaluations are also directly readable under `results/ai`; a saved response is a real recorded experiment, not a summary standing in for model output. `scripts/prepare_ai_inputs.py` can prepare a separate new experiment, while `scripts/evaluate_ai.py` recomputes the canonical saved response's quality and agreement scores.

See [reproducibility.md](../docs/reproducibility.md) for the distinction between restoring/validating data, recomputing classical results and performing a new live AI recovery.
