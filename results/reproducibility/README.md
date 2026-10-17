# Revised study: genuine clean-checkout verification

The published revised study at commit [`f7b3a9306f072fc95137db031da2428ee70ecfb7`](https://github.com/ckontz01/software-evolution-ex1/commit/f7b3a9306f072fc95137db031da2428ee70ecfb7) was cloned from GitHub into a new directory and verified on its first complete verification run. Its Git tree was `8210d30e61377dcc33302dc7b662d24cd0f448d5`.

This directory contains **new V2 evidence**. It replaces the previous V1 verification record as a unit; that earlier record remains in Git history and the original-study reference. The commit adding this directory records the verification of the commit above. It does not retroactively claim that the later evidence-only commit was the commit executed.

## What passed

- The checkout was clean, had no expanded data/build cache, and every one of its **246 committed files matched its Git blob bytes** before execution.
- All **32 study archives and 2,385 archived members** were restored with matching checksums.
- All **90 pinned Maven artifacts**, both immutable endpoint Git/source-JAR comparisons, and the deterministic **30 distinct release-family selection** passed offline checks.
- All **60 focused tests** passed using the real compiled Java tools.
- The independent validator passed **8,348,851 checks with zero failures**, including all 30 graphs, 120 final partitions, the pilot calibration, both directions of MoJoFM, and the recorded AI experiment.
- A new extraction of **Guava 33.7.2** and a new UE/A1/A2/A3/A4 execution reproduced **all 62 compared deterministic files byte for byte**. The resulting graph had **594 owned canonical types and 2,750 directed dependencies**; UE removed **22 classes**, leaving **572 types and 1,724 dependencies**.
- The new scoped instructor input also preserved **all 1,948 original binary class entries byte for byte**. This checks original bytecode directly, in addition to matching the complete derived JAR.
- The regenerated AI evaluation and other deterministic audit outputs matched the saved results: **13 exact byte comparisons**, plus **three complete JSON comparisons after excluding only their recorded audit timestamp**. No AI response was generated or optimized during verification.
- Both published PDF paths retained their committed bytes and SHA256: `442be41ed1d12ddeb487c2e31825dfbabf483acf8c698a5e8d7419a5f9b4b371`.

The 12 recorded verification commands took approximately **43.9 seconds** in this environment. This excludes cloning and initial file checks and is an observed runtime, not a speed guarantee.

## Evidence files

`clone_record.json` and `clone.log` preserve the actual clone command, complete combined output, exit code, and observed commit/tree. `receipt.json` preserves the runner invocation, exact command arguments, environment, start/completion times, exit codes, full log hashes, and final status. The 12 numbered logs contain the actual stdout/stderr of those commands.

`committed_file_checksums.json` records the initial Git blob and SHA256 of each committed file. `independent_validation.json` is the complete newly generated audit result. `latest_reproduction.json` lists each of the 62 byte comparisons and explicitly identifies the omitted timing/path metadata. `original_class_byte_checks.csv` gives the per-entry source/scoped hashes. `recomputed_output_comparisons.json` records the 16 audit/AI output comparisons.

`reproduction_evidence.zip` preserves the complete new latest-release `work/` tree, the saved `reference/` output bytes, and the newly generated `recomputed/` audit/AI outputs. It includes extraction and clustering execution logs and metadata even where those files were excluded from deterministic comparison. ZIP entry timestamps are fixed for packaging; actual execution times are in the receipt. `evidence_manifest.json` records all packaged member hashes and the top-level evidence hashes.

## Reproduce the check

Clone the desired published commit into a new directory. With the Python dependencies installed and Java 17+ available, run the repository's portable verifier:

```bash
EVOLUTION_JAVA=/path/to/java python3 scripts/verify_clean_checkout.py \
  --expected-commit f7b3a9306f072fc95137db031da2428ee70ecfb7 \
  --output /path/to/new/evidence
```

The output directory must be new or empty; keep it outside the clone. The verifier requires the supplied full commit SHA to equal `HEAD` and refuses an already expanded or modified checkout. It performs no clone, fetch, package installation, or parameter selection. The tool JARs are bundled and verified before the tool helper runs; artifact verification uses the preserved offline archives. The full command sequence is in the receipt.

## Scope of the conclusion

This is a repeat execution of the published implementation plus a separate independent mathematical/artifact audit. All 30 saved results are audited, while the latest release is additionally re-extracted and re-clustered. The two latest temporal comparisons use the preceding release's archived graph and partitions as their stated reference. The pilot k calibration is reused without another k search. This verification run is excluded from the 120 finalized study architectures.

Only acquisition mode/timestamps and the three audit timestamps changed among tracked files. All substantive outputs, implementation files, archives and PDFs remained unchanged. Successful reproduction establishes consistency and reproducibility of this declared static model; it does not establish intended-architecture ground truth, complete runtime behavior, or correctness of every possible extractor interpretation.
