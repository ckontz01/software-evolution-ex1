# Complete code and two-person handoff

Start with **[the commit map](../docs/commit_roadmap.md)**. It assigns six ordered commits to each student and links to the complete source for every step.

- [Full code in one HTML file](full_code.html): download and open locally; plain black-and-white typography, expandable source files and a commit index.
- [Per-commit code guides](code/): exact commands, full source listings and every payload path.
- [File inventory](file_inventory.csv): all 295 study files, assigned exactly once.
- [Source manifest](manifest.json): the pinned source tree, owners, complete hashes, code-listing scope and stage checks.
- [Download manifest](download_manifest.json): sizes and SHA-256 values of the complete generated student/packet ZIPs.
- [Handoff validation](verification.json): checks of bundle contents, whole-code listings and sequential imports. These checks concern delivery; the study's 91 tests and scientific evidence remain separately recorded.

Run `python handoff/build_handoff.py` from the repository root to generate the complete student ZIPs under `handoff/downloads/`. The generator needs only Python and Git. A shallow clone may first need `git fetch --depth 1 origin f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`.

`student_A_complete.zip` contains packets 01, 03, 05, 07, 09 and 11. `student_B_complete.zip` contains 02, 04, 06, 08, 10 and 12. Each packet includes the **actual complete files**, not patches or placeholders. Both students also receive every code listing for reciprocal review. The smaller `complete_code_guide.zip` contains all source/configuration files and guides, without the large evidence/tool/report payloads.

The source is the validated study at `f32e6e831f976eed8bf01faa1d66dbdc34bc49c7`. The 295 frozen payload files preserve the report's original source identities, including the short roadmap present at report generation. The current outer map is the handoff timetable. No scientific results were recomputed to divide the files.

The helper performs a dry run by default. `--apply` copies absent files after full validation; `--stage` also stages only the packet paths and verifies the index. It requires earlier packets to be committed, refuses differing files and supports a study subdirectory to preserve instructor files. It never commits or pushes. Use each student's real identity and dates, and identify the imported work as AI-assisted preparation.
