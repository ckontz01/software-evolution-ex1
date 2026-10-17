# Complete study data

The ZIP files preserve all **90 original Maven artifacts**, the two immutable endpoint Git source archives, and every computed per-release file: merged classes, alias mappings, typed and member dependencies, filtered graphs, removal decisions, A1–A4 partitions, metric terms, and original ACDC input/output/logs. No evidence was removed to make the repository smaller. The pilot and endpoint Git archives are preserved separately.

Run from the repository root:

```bash
python scripts/unpack_data.py
```

This verifies each archive and each member's SHA-256 before restoring `data/raw`, `data/graphs`, `data/upstream_git`, `results/versions`, and `results/pilot`. Matching existing files are left in place. A different existing file causes an error so a local rerun cannot silently be overwritten.

Use `--version 33.7.2` to restore one release, or `--verify-only` to audit every stored byte without writing. `manifest.json` lists every member and its hash. Archives have fixed timestamps and sorted paths, so `python scripts/package_data.py` recreates them deterministically from an unchanged working dataset.

The summary tables, charts, manifest, provenance, source code, report, and explanations are available as ordinary repository files. The archives keep the much larger detailed evidence together by release. After extraction, all documented scripts use ordinary CSV, JSON, RSF, JAR and source-JAR files.
