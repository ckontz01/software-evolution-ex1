# Fresh-checkout verification proof

**Passed for published source commit `ed18113b1641481585ca9695312842d05d903a70`.** This directory preserves the actual proof from a fresh public clone of that exact commit. The later evidence-only commit that adds this directory is **not** the commit tested by this run.

The complete verifier command ran on 17 October 2026 in **47.5 seconds** (47.503 seconds from the receipt's UTC start/end times). Its 12 child-command durations sum to 46.779 seconds. These are measured execution times on the recorded machine, not a general performance estimate.

## Verified scope

| Check | Result |
|---|---|
| Initial and final Git commit | `ed18113b1641481585ca9695312842d05d903a70` |
| Committed files checked against Git objects | 259 |
| Command stages | 12 passed; every exit code 0 |
| Correctness tests | 91 passed |
| Independent validation of the complete 30-release study | 7,949,858 checks; zero failures |
| Restored study evidence | 2,385 members in 32 logical ZIPs |
| Latest-release deterministic file comparisons | 62 byte-identical comparisons |
| Recomputed derived-output comparisons | 13 byte-identical; 3 equal after excluding only the recorded audit timestamps |
| Original class-file bytes | 1,948 checks passed |
| Published report PDFs | Both unchanged from committed bytes |

The repeat execution re-extracted Guava 33.7.2, recomputed usage equality and regenerated its four recovery conditions using the frozen pilot calibration. It reproduced 594 classes and 2,750 dependencies; filtering retained 572 classes and 1,724 dependencies. This extra verification run is excluded from the finalized study's 120 architectures. Independent validation covered all 30 releases; the repeat extraction covered the latest release. The AI stage reevaluated the preserved model response and did not perform a new model run.

## What is preserved

`receipt.json` records the environment, commands, timings, checksums and permitted variable audit changes. The 12 numbered logs are the original command logs. `clone_record.json` records the public clone and source commit. `committed_file_checksums.json`, `latest_reproduction.json`, `original_class_byte_checks.csv` and `recomputed_output_comparisons.json` preserve the detailed comparisons. `independent_validation.json` is the actual validator output generated in the fresh clone.

`runtime/` preserves the small extraction and architecture commands, logs, provenance and run records excluded from strict byte comparison because they can contain timings or absolute execution paths. Four declared variable audit outputs changed during verification; the receipt identifies each change and confirms it was permitted. A single untracked transfer staging file was preserved outside the clone before the pristine preflight; no committed file was changed during that cleanup.

The deterministic reproduced bytes remain available in the existing [study archives](../../archives/README.md) and their published summaries. This compact proof does not duplicate the full generated `work/` or `reference/` trees. Absolute paths inside the original receipts identify the execution environment; they are retained as observed. Runtime subsets from the original `work/` tree are copied under `runtime/` here.

`evidence_manifest.json` lists the actual relative path, byte count and SHA-256 of every proof file except the manifest itself. All copied evidence retains its original bytes. The implementation and exact rerun command are documented in [verify_clean_checkout.py](../../scripts/verify_clean_checkout.py).
