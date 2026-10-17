# Two-person contribution and commit roadmap

Working deadline: **23 October 2026, 23:59, Asia/Nicosia**, from tutorial slide 2. The introduction's earlier timetable is marked provisional. Use the latest Blackboard announcement if the instructor changes this deadline.

The study subject is **google/guava**. The destination used to prepare this work is **ckontz01/software-evolution-ex1**. The teacher-owned repository is a separate destination; its URL has not been supplied in this conversation.

## What the present commits mean

The initial implementation and documentation are AI-assisted preparation, committed through the authenticated account. They are not evidence that both students have already performed the tasks below. Neither authorship nor dates are fabricated. The assignment assesses each student's real contribution, so both students should review, reproduce, improve and explain their assigned parts, and make their own subsequent commits from their own accounts.

The roles below are a proposed balanced division: **Student A = Christoforos Kontzias** and **Student B = the teammate**. Replace the role label with the teammate's name when they join. Review ownership is reciprocal: every substantial change gets checked by the other student.

## Timetable

Dates are planned work sessions, not scheduled automatic commits. Commit a coherent result after the work and checks actually happen. A short written explanation or a corrected test is a valid result; an empty commit or a cosmetic change made only to simulate activity is not useful evidence.

| Date | Student A: implementation and evidence | Student B: implementation and evidence | Review checkpoint / suggested commits |
|---|---|---|---|
| 17 October | Read the assignment; verify the Guava release sample, tag SHAs, JRE choice and artifact hashes. Trace one JAR back to its source. | Read the UE paper; reproduce one dedication/equality example by hand; inspect boundary tests and the original-JNode distinction. | A: `docs: verify release provenance and scope`; B: `test: explain UE boundary and member-count cases`. |
| 18 October | Run the extraction fixture; trace inheritance, a call, a field reference and an inner/anonymous class into CSV evidence. Review exclusions. | Re-run UE tests and performance measurements; inspect strongest-caller evidence for several retained/removed Guava classes. | A: `test: validate bytecode extraction and class merging`; B: `docs: validate omnipresent decisions on Guava`. |
| 19 October | Inspect official ACDC source and pilot outputs; explain patterns, orphan adoption, the subgraph-size parameter and isolated nodes. | Reconstruct one k-means feature row; explain normalization, the fixed k rule, requested/actual k and reproducibility. | A: `docs: justify ACDC pilot configuration`; B: `docs: verify fixed feature and k policy`. |
| 20 October | Execute the 30-version pipeline and reconcile all class, member and edge counts with the manifest. Investigate one change point. | Hand-check lecture cohesion/coupling/MQ on the toy example; audit all 120 partitions and common-node comparisons. | A: `data: reproduce longitudinal extraction and partitions`; B: `test: audit metrics and partition coverage`. |
| 21 October | Relate measured growth/change to release evidence and the limits of Lehman's laws. Check every factual claim's source. | Read the actual latest-version AI evidence, prompts and partitions; verify membership and assess semantic grouping versus structural metrics. | A: `docs: explain evolution with release evidence`; B: `docs: critically review AI architecture recovery`. |
| 22 October | Review the teammate's detector/metrics explanations and challenge one assumption. Check report tables against machine-readable data. | Review the teammate's extraction/ACDC explanations and challenge one assumption. Check plots, captions and report readability. | Both: separate, meaningful review fixes; each records what they checked in `contributions.md`. |
| 23 October | Perform a clean regeneration and check the teacher repository contains the required data and code. | Verify the final PDF, bibliography, AI disclosure and oral-exam explanations; check the Blackboard submission package. | Both: final review; submit code/data to the teacher repository and PDF to Blackboard before 23:59. Leave a time buffer. |

## A sensible division of the code

| Work area | Primary understanding/review owner | Cross-review owner |
|---|---|---|
| Release acquisition, hashes, source ownership, dependency extractor | Student A | Student B |
| UE formulas, detector, exact oracle, benchmark | Student B | Student A |
| ACDC input, flags, output parsing, pilot | Student A | Student B |
| k-means features and k, lecture quality metrics | Student B | Student A |
| Longitudinal execution, growth graphs, release explanations | Student A | Student B |
| Latest-version AI comparison, threats to validity | Student B | Student A |
| Final report, reproducibility and oral exam | Both | Both |

## Working in Git

Clone the temporary repository and install/run the documented checks. Each student then creates a branch for a concrete task, makes and tests their own changes, and opens a reviewable pull request or follows the teacher's required Git workflow. Use the correct account and Git identity on each student's computer. Do not rewrite the preparation commits to make them appear authored by a different person.

Keep the teacher repository's existing history. When its URL is available, inspect it before deciding how to bring in the preparation work; do not force-push or replace instructor-provided files. Record the initial import as AI-assisted preparation, then make the genuine periodic development/review commits. This document does not send invitations, emails, or messages, and does not create future automatic commits.

## What both people should be able to do without reading a script

1. Explain why a tag, a published artifact version and a commit SHA are related but different identifiers.
2. Draw one class-to-class edge from a real bytecode reference and show the exact CSV row.
3. Explain why `$` classes are merged using enclosing metadata and why original member IDs remain distinct.
4. Derive UE for a ten-caller utility and for a utility with one special setup caller.
5. Build one feature row, state k, and explain why a high MQ does not prove the intended architecture has been recovered.
6. State which result they personally verified, what they found, and how their teammate checked it.
