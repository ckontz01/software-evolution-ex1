# Project selection: Guava (revised study)

The user explicitly selected [google/guava](https://github.com/google/guava). The revised study analyzes the production Guava JRE library across **30 distinct major/minor version families**, from **10.0 to 33.7.2**. Each family contributes exactly one release. The complete immutable artifact manifest is [config/versions.json](../config/versions.json).

Guava supplies collections, concurrency utilities, caching, graph structures, input/output, hashing, primitive helpers, strings, and other Java utilities. Its official [README](https://github.com/google/guava) describes its scope and JRE/Android variants. [Guava Explained](https://github.com/google/guava/wiki) provides functional documentation; it is not a measured architecture ground truth.

## Assignment eligibility

| Requirement | Verified evidence |
|---|---|
| Java project hosted on GitHub | Captured repository metadata records Java; preserved sources and artifacts are Java. |
| At least 10 major/minor versions | The revised sample contains exactly 30 distinct major/minor families, selected from 45 eligible families. |
| At least 10,000 source lines in the latest release | The owned 33.7.2 source prefixes contain 96,622 nonblank, noncomment physical Java lines. The complete source JAR has 96,646, including the module descriptor. |
| Not archived | GitHub metadata records archived=false at the frozen 2026-10-17 snapshot. |
| At least 50 commits since 2024-01-01 | A stored API response sample contains 100 distinct commits satisfying that date bound. This is a verified lower bound, not the total number of commits. |
| Not a fork | GitHub metadata records fork=false. |
| Created before 2024 | Repository creation is 2014-05-29T16:23:17Z. The imported source history predates GitHub repository creation. |

Evidence: [project_eligibility.json](../data/provenance/project_eligibility.json), [family_selection.json](../data/provenance/family_selection.json), [tag_inventory.json](../data/provenance/tag_inventory.json), and [latest source inventory](../data/provenance/source_inventory_33.7.2.json).

The assignment asks students to obtain instructor approval for the project. No such approval was provided in the conversation, so this repository does not claim it has been obtained. User selection and instructor approval are distinct records.

## Why the selection rule changed

The first study sampled evenly by individual release rank. That gave the frequently patched 33.4 family four observations and the 33.7 family two, leaving only 26 distinct families among 30 releases. The revised rule samples **families first**, eliminating that overrepresentation. A patch such as 32.1.3 is the sole representative of its family, rather than one of several 32.1 observations.

The revised selection was frozen before revised graphs or quality scores were calculated. It does not discard releases because they have identical graphs or inconvenient results. Structural stability is a valid measured outcome, not a selection failure.

## Reproducible selection rule

[scripts/select_versions.py](../scripts/select_versions.py) uses only the captured release catalog. It reads no source changes, dependency graphs, clusters, or quality scores.

1. Begin with the public tag snapshot captured on **2026-10-17**: 124 tag references, of which 82 match plain numeric main-project tags of the form `vMAJOR.MINOR[.PATCH]`. The remaining 42 include prereleases, auxiliary-component tags, backports, and alternate tag names; they are not all beta releases.
2. Retain the numeric Maven era beginning at 10.0. Nine earlier numeric tags are outside the declared period. Retain the three previously documented mainline exclusions: ambiguous `v13.0`/`v13.0-final`, and the 23.6.1/24.1.1 maintenance releases published after the newer 25.0 line. This leaves **70 eligible mainline releases**.
3. Group eligible releases by `MAJOR.MINOR`. Order the resulting **45 families** by their first eligible release date, with numeric family order as a deterministic tie-break.
4. Choose zero-based family ranks `round(i * 44 / 29)` for `i = 0, ..., 29`. The implementation uses exact rational arithmetic. The 30 chosen ranks are `0, 2, 3, 5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24, 26, 27, 29, 30, 32, 33, 35, 36, 38, 39, 41, 42, 44`.
5. Select the highest eligible stable patch in each chosen family. Declare one fixed endpoint exception: the first family uses **10.0**, its oldest release, to anchor the beginning of the study period. The last family uses **33.7.2**, its latest eligible stable release. This exception is explicit in the manifest and selector; it is not based on a structural result.
6. Use the plain Maven Guava artifact before 23.1 and the `-jre` artifact from 23.1 onward. The `-android` flavor is a platform variant, not a separate release observation.
7. Verify the exact version sequence, 30 distinct families, captured tag/commit identities, increasing release dates, and the actual intervening stable-release names. No chosen family may appear twice.

The rule is spaced in **family rank**, not uniform in calendar time. Some selected families are adjacent. With 30 observations from 45 families, it is impossible to omit at least one family between every pair: that would require at least 59 available families. The study therefore does not claim that every neighboring selected family is separated by an omitted family, or that every pair of observations has the same elapsed duration. It does ensure broad coverage of the full eligible history without repeatedly sampling patch families.

Fifteen eligible families are unselected. The chosen families contribute 30 releases, leaving 40 eligible individual releases unsampled. Every family, candidate patch, selected rank, and representative decision is recorded in [family_selection.json](../data/provenance/family_selection.json).

To verify the frozen selection without changing it:

```bash
python scripts/select_versions.py --check
```

To regenerate the same manifest from the same catalog while preserving existing artifact checksum pins:

```bash
python scripts/select_versions.py --write
```

The generation command does not refresh the catalog from the internet. A future cutoff or a changed sample is a new study configuration, not a transparent replacement for these results.

## The selected sample

| # | Guava release | Major/minor family | Maven artifact version | Release date | Family rank (zero-based) |
|---:|---|---|---|---|---:|
| 1 | 10.0 | 10.0 | 10.0 | 2011-09-28 | 0 |
| 2 | 12.0.1 | 12.0 | 12.0.1 | 2012-07-10 | 2 |
| 3 | 13.0.1 | 13.0 | 13.0.1 | 2012-08-28 | 3 |
| 4 | 15.0 | 15.0 | 15.0 | 2013-09-06 | 5 |
| 5 | 16.0.1 | 16.0 | 16.0.1 | 2014-02-03 | 6 |
| 6 | 18.0 | 18.0 | 18.0 | 2014-08-25 | 8 |
| 7 | 19.0 | 19.0 | 19.0 | 2015-12-09 | 9 |
| 8 | 21.0 | 21.0 | 21.0 | 2017-01-12 | 11 |
| 9 | 22.0 | 22.0 | 22.0 | 2017-05-22 | 12 |
| 10 | 23.1 | 23.1 | 23.1-jre | 2017-09-27 | 14 |
| 11 | 23.2 | 23.2 | 23.2-jre | 2017-10-11 | 15 |
| 12 | 23.4 | 23.4 | 23.4-jre | 2017-11-09 | 17 |
| 13 | 23.5 | 23.5 | 23.5-jre | 2017-11-22 | 18 |
| 14 | 24.0 | 24.0 | 24.0-jre | 2018-02-01 | 20 |
| 15 | 24.1 | 24.1 | 24.1-jre | 2018-03-15 | 21 |
| 16 | 25.1 | 25.1 | 25.1-jre | 2018-05-31 | 23 |
| 17 | 26.0 | 26.0 | 26.0-jre | 2018-08-01 | 24 |
| 18 | 27.1 | 27.1 | 27.1-jre | 2019-03-08 | 26 |
| 19 | 28.0 | 28.0 | 28.0-jre | 2019-06-12 | 27 |
| 20 | 28.2 | 28.2 | 28.2-jre | 2019-12-27 | 29 |
| 21 | 29.0 | 29.0 | 29.0-jre | 2020-04-13 | 30 |
| 22 | 30.1.1 | 30.1 | 30.1.1-jre | 2021-03-19 | 32 |
| 23 | 31.0.1 | 31.0 | 31.0.1-jre | 2021-09-27 | 33 |
| 24 | 32.0.1 | 32.0 | 32.0.1-jre | 2023-06-09 | 35 |
| 25 | 32.1.3 | 32.1 | 32.1.3-jre | 2023-10-10 | 36 |
| 26 | 33.1.0 | 33.1 | 33.1.0-jre | 2024-03-13 | 38 |
| 27 | 33.2.1 | 33.2 | 33.2.1-jre | 2024-05-31 | 39 |
| 28 | 33.4.8 | 33.4 | 33.4.8-jre | 2025-04-14 | 41 |
| 29 | 33.5.0 | 33.5 | 33.5.0-jre | 2025-09-17 | 42 |
| 30 | 33.7.2 | 33.7 | 33.7.2-jre | 2026-09-29 | 44 |

The manifest stores the full commit SHA, tag, artifact URLs, SHA-256 and Maven SHA-1 pins, skipped stable release names, and omitted family names. Dates through 23.0 are calendar dates from the project's [ReleaseHistory](https://github.com/google/guava/wiki/ReleaseHistory) and individual release notes; later dates use `GitHub Release.published_at`. Git commit timestamps are retained separately. A lightweight tag has no independent tagger timestamp.

## Project ownership and external dependencies

The input scope is the **production Guava JRE artifact**, not every module in the Git repository. Android, GWT, test libraries, benchmarks, and separately published compatibility artifacts are outside the target variant.

Project-owned production sources under both `com.google.common` and `com.google.thirdparty.publicsuffix` are included. The public-suffix Java implementation is distributed as Guava source and carries Guava Authors copyright headers. Its package name is not evidence that it is an external library. The provenance of public-suffix list data is a separate question from ownership of the Java implementation using that data.

The earlier namespace-only study excluded this support package. Including it avoids treating a move from `com.google.common.net.TrieParser` to `com.google.thirdparty.publicsuffix.TrieParser` as loss of functionality from Guava. The study still cannot automatically identify every rename across versions; class identity is based on canonical names.

JDK classes, failureaccess, external annotation libraries, and other external endpoints are excluded. A dependency is retained only when both endpoints belong to the retained project class universe. Instructor extraction and the annotation policy are specified separately in [modeling_decisions.md](modeling_decisions.md); this document defines artifact and source ownership, not which relationship kinds a tool can observe.

“Exclude beta versions” refers to prerelease distributions. The presence of Guava's `@Beta` annotation on a class within a stable release does not remove that first-party class from the study.

This is one longitudinal case study of a declared artifact, scope, and measurement process. Its results do not establish universal software-evolution laws.
