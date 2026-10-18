# Verification of the cleaned current study

**Passed for cleaned source commit [`7774d4e57033e519698749de8ecca514bcb57040`](https://github.com/ckontz01/software-evolution-ex1/commit/7774d4e57033e519698749de8ecca514bcb57040).** This directory preserves the actual proof from a new Git checkout of that exact commit. The later commit adding this evidence directory is not the source commit tested by this run.

The checkout began with `git clone --no-hardlinks` from the local Git repository. Its first detached checkout could not read the newly created commit tree, so the exact cleaned commit was fetched directly from the public GitHub preparation repository before the successful checkout. The initial failure and successful retry are retained in the clone log and command record. No source working-tree files, expanded datasets or build caches were copied. This proves a fresh checkout of the recorded Git objects; it does not claim a second download of every unchanged object from GitHub.

The verifier ran on **18 October 2026** in **65.025 seconds**, measured between the receipt's UTC start and completion timestamps. The 11 child-command durations sum to **63.985 seconds**. These are measured times on the recorded machine.

## Verified scope

| Check | Result |
|---|---|
| Initial and final Git commit | `7774d4e57033e519698749de8ecca514bcb57040` |
| Committed files checked against Git objects | 228 |
| Command stages | 11 passed; every exit code 0 |
| Correctness tests | 91 passed |
| Independent audit of all 30 releases | 7,949,858 evidence checks; zero failures |
| Restored study evidence | 2,385 members in 32 logical ZIPs |
| Latest-release deterministic files | 62 byte-identical comparisons |
| Recomputed derived outputs | 12 byte-identical; 3 equal after excluding only recorded audit timestamps |
| Original class-file bytes | 1,948 checks passed |
| Report PDFs | Both unchanged from committed bytes |

The repeat execution re-extracted Guava **33.7.2**, computed Usage Equality and regenerated A1–A4 using the recorded pilot calibration. It reproduced **594 classes and 2,750 dependencies**; filtering retained **572 classes and 1,724 dependencies**. This verification run is excluded from the study's 120 final architectures. The independent audit covered all selected releases; fresh extraction and clustering covered the latest release. The AI stage reevaluated the actual saved model response without making another model call.

## What the files preserve

`receipt.json` records the exact source commit, environment, commands, timings, checksums and permitted audit-output changes. The 11 numbered logs contain the original command output. `clone_record.json` and `clone.log` preserve checkout preparation. The runner's `committed_file_checksums.json` checks every committed working file against its Git object. `latest_reproduction.json`, `original_class_byte_checks.csv` and `recomputed_output_comparisons.json` preserve the actual comparisons. `independent_validation.json` is the validator output produced in the fresh checkout.

`runtime/` preserves the small extraction and architecture command records, logs, provenance and run metadata excluded from strict byte comparisons because they contain timings or absolute execution paths. **4 declared variable audit outputs** changed during verification; the receipt identifies every changed path and verifies that it was permitted. No checkout-residue intervention was necessary before the pristine preflight.

All copied evidence retains its original bytes, including observed timestamps and absolute paths. No old baseline, obsolete revision-audit output or earlier checkout receipt was imported into this directory. The deterministic input and result bytes are already preserved in the [study archives](../../archives/README.md), so this proof does not duplicate the complete generated `work/` and `reference/` trees. Their comparison hashes remain in the receipt; the selected runtime files from `work/` are copied under `runtime/`.

`evidence_manifest.json` lists the relative path, byte count and SHA-256 of every proof file except itself. To repeat the workflow, use [scripts/verify_clean_checkout.py](../../scripts/verify_clean_checkout.py) from a fresh checkout and supply its exact commit SHA with a new output directory. Copying this proof into a teacher repository is not a fresh verification of that different checkout.
