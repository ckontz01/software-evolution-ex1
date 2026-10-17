# EPL484 — Software Architecture Evolution

A reproducible, AI-assisted study of **30 spaced stable Jackson Core releases**, prepared for the Software Evolution course.

## Study contract

- Sample 30 stable, nonconsecutive releases; pin source commits and source/binary artifacts.
- Exclude external and shaded third-party libraries; merge inner and anonymous classes into their enclosing top-level class.
- Preserve all seven tutorial dependency categories and document every modeling choice.
- Implement the **usage equality (UE)** method from Yano and Matsuo (ICSME 2020) as the requested replacement for the supplied JNode. UE is distinct from the lecture's original ComponentRank/Noise method.
- Produce one finalized A1/A2/A3/A4 architecture per release: ACDC and k-means, each with and without detected omnipresent classes.
- Report the lecture's cohesion, coupling, and MQ, with cluster sizes and node/edge coverage.
- Recover and discuss an AI architecture for the latest selected release with recorded inputs and prompts.
- Provide a PDF report, reproducibility instructions, oral-exam explanations, and an honest two-person contribution roadmap.

## Authorship and course handoff

This repository is a temporary **AI-assisted preparation workspace**. Present-day commits are made through the authenticated account. The two students must review, understand, validate, and document their own contributions before transferring work to the teacher-owned repository. No teammate authorship or historical activity is implied.

Project approval by the instructor is not established by this repository. The sample uses Jackson Core because the earlier Spring AI candidate cannot meet the requested release coverage.

Implementation, executed results, and the final report are added in subsequent commits.
