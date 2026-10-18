# Two-person commit map — with the complete code

This map gives each of you **six ordered commits**, the **whole files to push**, the checks to run and the part you should be able to explain in the oral exam. The full assignment is covered: **295 files**, including all code, configuration, tools, data, results and the report.

**Student A: Christoforos Kontzias. Student B: your teammate.** Each student uses their own account and Git identity. The dates below are planned work sessions from **18 to 23 October 2026**, not a record of work already done. The deadline in the attached tutorial, slide 2, is **23 October 2026, 23:59, Asia/Nicosia**; follow any later announcement from the instructor.

## Open the code or use the ready-made files

- **[Open the complete code guide](../handoff/full_code.html):** one plain black-and-white HTML file containing all **61 code and configuration files in full**. Download it and open it in a browser; use the commit index and expand the files you want to read.
- **The “Whole code” links in the table below:** each opens that commit's complete source listings, exact file inventory, checks and Git commands. These also render directly on GitHub.
- **`student_A_complete.zip` and `student_B_complete.zip`:** each contains the actual files for that student's six commits, organised into `packets/<commit>/payload/`. There are no omitted source files or placeholder functions. Both ZIPs also contain the full guide so you can review each other's work.
- **`complete_code_guide.zip`:** a smaller download containing the guide and all 61 actual source/configuration files, grouped by commit. Use the complete student ZIPs when importing the data, tools and report as well.
- **[File inventory](../handoff/file_inventory.csv)** and **[manifest](../handoff/manifest.json):** the owner, packet, original size and hashes of every one of the 295 study files.

The downloads are attached to the delivery message. They can also be rebuilt from the temporary repository using `python handoff/build_handoff.py`; see “Rebuild the downloads” below. Large ZIPs are generated locally so the Git repository does not contain a second copy of the preserved dataset.

The packets reproduce the validated study snapshot **`f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`**, including its original documentation. **Use this outer handoff guide for the current sequence and timetable.** The original short roadmap inside packet 10 is kept byte-for-byte because the report records its source hashes. The expanded guide does not change the scientific code, the selected releases or any reported measurement.

The source is AI-assisted preparation. An import commit records who actually imported and checked a packet; it does not claim that person originally wrote every line. Add a short commit-message paragraph about what you personally checked and found. Keep imported study files unchanged during this sequence so later packets can verify their predecessors. After the import, make genuine review fixes and fill in the contribution log with the actual commits and dates.

## The six-day map

Follow the shared order **01 → 02 → … → 12**. Student B waits for A's preceding commit; Student A then pulls B's work before the next packet. The division follows the code's dependencies, so each stage's advertised checks have the files they need.

| Planned date | Commit | Person | What that person pushes | Files | Whole code and exact commands |
|---|---:|---|---|---:|---|
| 18 Oct | 01 | A | Project setup, requirements, analysis configuration, graph utilities, release selector and selection evidence | 14 | [01 — Setup and versions](../handoff/code/01-a-setup.md) |
| 18 Oct | 02 | B | Paper-based Usage Equality detector, JNode-UE CLI, exact tests, benchmark and explanation | 6 | [02 — Usage Equality](../handoff/code/02-b-usage-equality.md) |
| 19 Oct | 03 | A | Instructor extractor JAR, supplemental Java extractor, Python adapter, toolchain, complete official ACDC source and extractor tests | 37 | [03 — Extraction and Java](../handoff/code/03-a-extraction.md) |
| 19 Oct | 04 | B | Lecture cohesion, coupling and MQ; directional MoJoFM; metric tests and explanation | 5 | [04 — MQ and MoJoFM](../handoff/code/04-b-metrics.md) |
| 20 Oct | 05 | A | Data acquisition, all 32 preserved archives, provenance and inventories, graph summaries, packaging/restoration code and tests | 75 | [05 — Data and archives](../handoff/code/05-a-data.md) |
| 20 Oct | 06 | B | ACDC adapter, k-means features, pilot k selection, clustering tests and pilot decision | 5 | [06 — Clustering and k](../handoff/code/06-b-clustering.md) |
| 21 Oct | 07 | A | The 30-version study runner, exploratory runner and recorded aggregate result tables | 10 | [07 — Study execution](../handoff/code/07-a-study.md) |
| 21 Oct | 08 | B | The complete recorded AI architecture experiment, its inputs and response, evaluation code and reflection | 28 | [08 — AI evaluation](../handoff/code/08-b-ai-evaluation.md) |
| 22 Oct | 09 | A | Evolution and revision audits, preserved first baseline, change-point evidence and interpretation | 15 | [09 — Evolution audits](../handoff/code/09-a-evolution-audits.md) |
| 22 Oct | 10 | B | Independent validation, real UE case audit, README, methods, oral-exam guide and remaining study documentation | 12 | [10 — Validation and explanations](../handoff/code/10-b-validation-docs.md) |
| 23 Oct | 11 | A | Report generator, both final PDFs, all figures and report provenance | 28 | [11 — Report and figures](../handoff/code/11-a-report.md) |
| 23 Oct | 12 | B | Clean-checkout verification code and the complete preserved reproduction evidence | 60 | [12 — Reproducibility](../handoff/code/12-b-reproducibility.md) |

Student A has **179 files** and Student B has **116 files**. The size difference is mostly the preserved 30-version dataset in A's packet 05. Both have six substantive areas to review and explain. A imports the official ACDC Java source with the Java toolchain; B imports the Python clustering adapter and k-means policy. Both should understand how those pieces fit together.

The instructor supplied DependencyExtractor as a **compiled JAR**. That original JAR is included in packet 03. All available project and ACDC source code is printed in the guide; unavailable instructor source code is not invented. Upstream authorship and licences stay with the bundled files.

## Set up your own working copy

Extract your complete ZIP outside the teacher repository. It creates either a `student_A/` or `student_B/` directory. Open `START_HERE.md` there. The helper needs only Python; running the study checks needs **Python 3.12 with the locked dependencies and Java 17 or later**.

Use the actual teacher-owned repository URL below. It has not been provided in this conversation. The temporary preparation repository is [ckontz01/software-evolution-ex1](https://github.com/ckontz01/software-evolution-ex1); the project being analysed is [google/guava](https://github.com/google/guava).

```bash
git clone TEACHER_REPOSITORY_URL teacher-repo
cd teacher-repo
git config user.name
git config user.email
```

Check that these are your real details. If necessary, set your own name and email for this checkout. Each student does this on their own computer; do not change the identity to impersonate the other person.

Set two paths in your terminal. Replace the example paths with your own absolute paths:

```bash
export HANDOFF_DIR="/absolute/path/to/student_A"
export TEACHER_REPO="/absolute/path/to/teacher-repo"
```

Student B uses their extracted `student_B` directory for `HANDOFF_DIR`.

The commands here place the study inside a new **`guava-study/`** directory. This preserves an instructor's existing README, `.gitignore` and other starter files. If the teacher requires the assignment at the repository root, omit `--subdir guava-study` in every helper command and run study checks from the repository root. The helper stops if an existing file differs; resolve the required layout before importing, rather than replacing instructor files.

Use the branch required by the instructor. The example below uses a shared branch named `guava-assignment`; it can later be reviewed and merged through the teacher's normal workflow.

**Student A, before packet 01:**

```bash
git -C "$TEACHER_REPO" switch -c guava-assignment
```

**Student B, after A has committed and pushed packet 01:**

```bash
git -C "$TEACHER_REPO" fetch origin
git -C "$TEACHER_REPO" switch --track origin/guava-assignment
```

**Both students, before every later packet:**

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
```

## What to do for each commit

Each packet's linked guide has its own exact commands. This is the pattern, using A's packet 03 as an example:

```bash
# Check the destination, source hashes and all earlier committed packets.
# This first command only reports the plan; it writes nothing.
python "$HANDOFF_DIR/apply_packet.py" \
  --packet "$HANDOFF_DIR/packets/03-a-extraction" \
  --target "$TEACHER_REPO" --subdir guava-study

# Copy the complete packet after the checks succeed.
python "$HANDOFF_DIR/apply_packet.py" \
  --packet "$HANDOFF_DIR/packets/03-a-extraction" \
  --target "$TEACHER_REPO" --subdir guava-study --apply

# Run the checks listed in this packet's guide.
cd "$TEACHER_REPO/guava-study"
python scripts/fetch_tools.py
python scripts/build_java.py
PYTHONPATH=src python -m unittest discover -s tests -p 'test_extractor.py' -v

# Stage only this packet and verify the staged file contents.
python "$HANDOFF_DIR/apply_packet.py" \
  --packet "$HANDOFF_DIR/packets/03-a-extraction" \
  --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" \
  --packet "$HANDOFF_DIR/packets/03-a-extraction" \
  --target "$TEACHER_REPO" --subdir guava-study --check-staged

git -C "$TEACHER_REPO" commit \
  -m "import: add instructor extraction and complete Java toolchain (AI-assisted preparation)"
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

The helper checks every payload file and predecessor before copying. It copies only absent files, accepts identical existing files, rejects differing files and stages only the current packet's paths. It does not create commits, push, set identities or change history. If a packet is already committed unchanged, there is no new import commit to make.

After applying packet 01 and before its checks or commit, create your environment from the imported study directory. Student B does this after pulling packet 01:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
java -version
```

Keep that environment active for subsequent checks. Packet 03 includes the pinned compiler, ASM library and instructor JAR, so the Java tools do not need to be downloaded again. Packet 06 runs `python scripts/run_checks.py`: by that point all **91 study tests** are present, and the command builds Java first so the ACDC integration checks run.

Some study commands rewrite recorded timestamps or evidence. The packet guides identify these and keep them out of the ordinary import checks. Use a disposable copy for those commands. The incoming packet hashes deliberately refer to the preserved source; they should not change halfway through the sequence.

## Final verification after packet 12

First, commit and push all twelve packets. Then clone the actual teacher branch into a fresh directory. Use the teammate's complete bundle for the following check, because it contains packet 12:

```bash
git clone --branch guava-assignment TEACHER_REPOSITORY_URL teacher-check
export TEACHER_CHECK="/absolute/path/to/teacher-check"
export HANDOFF_B_DIR="/absolute/path/to/student_B"

python "$HANDOFF_B_DIR/apply_packet.py" \
  --packet "$HANDOFF_B_DIR/packets/12-b-reproducibility" \
  --target "$TEACHER_CHECK" --subdir guava-study

cd "$TEACHER_CHECK/guava-study"
python scripts/unpack_data.py
python scripts/run_checks.py
python scripts/validate_results.py \
  --output results/rerun/student-final-validation.json
git -C "$TEACHER_CHECK" rev-parse HEAD
git -C "$TEACHER_CHECK" status --short
```

The packet-12 dry run checks its files and every preceding packet against the actual committed checkout: all **295 original study files**, while allowing unrelated instructor files elsewhere. It should report that the packet is already present. The following commands restore the preserved evidence, run the study tests and write a fresh independent-validation result into an ignored directory. Record the actual commit, output and any findings in your contribution log.

The original `scripts/verify_clean_checkout.py` assumes the **study directory is the Git root**. Its full receipt command is available in packet 12's guide for that layout. For the nested `guava-study/` layout, use the commands above. The archived V2/V3 receipts retain the original preparation commits they verified; copying them is not a new verification of the teacher repository.

Once the exact import is complete, make your actual review improvements and contribution-log entries normally. If a change affects the method or results, rerun the relevant checks and update the report evidence. Submit through the teacher's required branch/PR and Blackboard workflow before the deadline, leaving a time buffer.

## Rebuild the downloads

The delivered ZIPs contain everything assigned to their owners. To recreate them from Git instead:

```bash
git clone https://github.com/ckontz01/software-evolution-ex1.git guava-preparation
cd guava-preparation
python handoff/build_handoff.py
```

This creates `handoff/downloads/student_A_complete.zip`, `student_B_complete.zip`, `complete_code_guide.zip` and twelve individual packet ZIPs. It reads immutable Git objects at the pinned study snapshot and verifies every payload's length, SHA-256, Git blob and ownership. It does not rerun the experiments or use the current working copy as a substitute for the frozen source.

If you used a shallow clone and the pinned commit is missing, fetch that exact commit before rebuilding:

```bash
git fetch --depth 1 origin f32e6e831f976eed8bf01faa1d66dbdc34bc49c7
python handoff/build_handoff.py
```

The recorded ZIP sizes and SHA-256 values are in [the download manifest](../handoff/download_manifest.json). The complete code guide, packet guides and file inventory remain directly available in GitHub; the large generated downloads are not duplicated in Git.

## Before the oral exam

For each of your six packets, be able to show one concrete input, follow it through the code and explain an output or test. Each packet starts with a specific review task. Both of you should also be able to explain the overall path from a Guava release to its scoped dependency graph, Usage Equality decisions, A1–A4 partitions, quality measurements and evolution plots.

Use the study's oral-exam guide for the detailed questions, and add your own examples from the checks you actually ran. The aim of the division is that each person can defend a substantial part of the work and understand how the other person's part connects to it.
