# Complete revised study data

The current bundles preserve all **90 original Maven artifacts** for the 30 selected families, two immutable endpoint Git source archives, and complete detailed graph/algorithm evidence. The archive manifest is authoritative for the current member counts and hashes. Original-study data remain recoverable from the original Git commit; unselected old releases are not extra observations in this revised series.

Each release bundle includes the complete original binary JAR, matching source JAR and POM; the source-owned class inventory and enclosing aliases; the deterministic instructor input JAR and per-class original-byte hashes; the unmodified instructor tool's raw CSV, command and log; normalized primary typed/binary relationships; separate supplemental graphs and member references; exclusions and unresolved evidence; UE scores and retained graph; all A1-A4 partitions, metric terms, ACDC inputs/outputs/logs, and directional MoJoFM comparison details.

The pilot bundle preserves all three ACDC trials, all 14 k-means inertia-grid candidate assignments and run records, the selected pilot partition, matched-ACDC-k diagnostic and frozen calibration. It is separate from the 120 final architectures. Endpoint Git archives support offline repetition of the oldest/latest source-JAR comparison.

Restore from the repository root:

```bash
python scripts/unpack_data.py
```

This checks every selected archive and member before restoring `data/raw`, `data/graphs`, `data/upstream_git`, `results/versions` and `results/pilot`. Existing matching files remain; a differing local file causes an error before restoration begins. Use `--version 33.7.2` to restore one release, or `--verify-only` to audit stored bytes without writing.

## Base64 storage

The schema-3 `manifest.json` describes **32 logical standard ZIP files**. The 30 release ZIPs and the pilot ZIP are each stored as one ASCII text file, such as `versions/guava-10.0.zip.b64`. This is ordinary padded RFC4648 base64 with no whitespace or line wrapping. Decoding it reconstructs the exact ZIP bytes; encoding does not recompress, alter or discard any evidence. Base64 text is approximately one third larger than its decoded bytes and supports reliable transfer of these complete bundles. `upstream_git.zip` remains a single unchanged binary ZIP file.

Every bundle retains its logical ZIP `path`, `bytes`, `sha256`, `member_count` and complete `members` list. A base64 bundle declares `storage: "base64"` and a separate `encoded_file` record with the stored text's `path`, `bytes`, `sha256` and `text_encoding: "ascii"`. Thus the stored text checksum and decoded ZIP checksum identify different byte sequences explicitly. Every original member still has its own path, byte count and SHA-256.

The normal restore command handles decoding automatically. It verifies the encoded text's size and checksum, performs strict canonical base64 decoding, verifies the decoded ZIP's size and checksum, and validates all original member paths, inventories and hashes. It checks all selected bundles and existing destinations before restoring any member. Missing or altered files, invalid base64, whitespace, noncanonical padding, absolute paths, traversal and symlink destinations are rejected. The same command still reads the earlier whole-ZIP and ordered 512 KiB multipart formats.

Fixed ZIP timestamps and sorted input paths allow `python scripts/package_data.py` to recreate deterministic bundles from unchanged files. It completes each ZIP before encoding it and replaces each encoded file atomically. The final manifest is also replaced atomically; superseded whole ZIPs and multipart storage are removed afterward. Superseded release detection includes whole ZIPs, encoded ZIPs and parts so an older cohort cannot silently enter the current sample.

The source code, summary tables, figures, configurations, acquisition provenance, report and documentation remain ordinary repository files. The recorded AI prompt/input/output and evaluations are also directly readable under `results/ai`; a saved response is a real recorded experiment, not a summary standing in for model output. `scripts/prepare_ai_inputs.py` can prepare a separate new experiment, while `scripts/evaluate_ai.py` recomputes the canonical saved response's quality and agreement scores.

See [reproducibility.md](../docs/reproducibility.md) for the distinction between restoring/validating data, recomputing classical results and performing a new live AI recovery.
