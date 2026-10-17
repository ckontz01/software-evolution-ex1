# Project selection: Guava

The user explicitly selected [google/guava](https://github.com/google/guava). This study analyzes the production Guava JRE library across 30 nonconsecutive stable releases, from 10.0 to 33.7.2. The complete immutable manifest is [config/versions.json](../config/versions.json).

Guava supplies reusable Java collections, concurrency utilities, caching, graph structures, input/output, hashing, primitive helpers, strings, and other utilities. Its official README describes both its scope and the JRE/Android artifact variants. Architecture documentation is available through [Guava Explained](https://github.com/google/guava/wiki) and the linked subsystem guides. Those guides are functional documentation rather than a measured architecture ground truth.

## Assignment eligibility

| Requirement | Verified evidence |
|---|---|
| Java project hosted on GitHub | The repository metadata records Java; public source and Maven artifacts are Java. |
| At least 10 major/minor versions | The selected sample spans 26 distinct major/minor version families. |
| At least 10,000 source lines in the latest release | The 33.7.2 source JAR contains 95,876 nonblank, noncomment Java lines under com.google.common. The full source JAR contains 96,646; the larger number includes the excluded public-suffix support and module descriptor. |
| Not archived | GitHub metadata: archived=false at the 2026-10-17 snapshot. |
| At least 50 commits since 2024-01-01 | A stored API response sample contains 100 distinct commits satisfying that date bound. This is a verified lower bound, not a claim that only 100 commits exist. |
| Not a fork | GitHub metadata: fork=false. |
| Created before 2024 | The GitHub repository creation timestamp is 2014-05-29T16:23:17Z. The source history predates the GitHub repository's creation. |

Evidence: [project_eligibility.json](../data/provenance/project_eligibility.json), [tag_inventory.json](../data/provenance/tag_inventory.json), and [latest source inventory](../data/provenance/source_inventory_33.7.2.json).

The assignment asks the students to obtain instructor approval for the chosen project. This repository does not assert that approval has been obtained: no instructor approval was supplied in the conversation. User selection and instructor approval are different records.

## How the 30 releases were selected

The release manifest was fixed before clustering results were computed. The rule uses release history alone, so high or low MQ values cannot influence which versions enter the study.

1. Read the public GitHub tag references and resolve each selected lightweight tag to its full immutable commit SHA.
2. Retain plain numeric main-project tags of the form vMAJOR.MINOR or vMAJOR.MINOR.PATCH. The snapshot has 124 total tag refs and 82 matching numeric stable refs. The remaining 42 refs include prereleases, auxiliary-component tags, backports, and alternate tag names; they are not all beta releases.
3. Start the historical study at 10.0. This yields a consistent numeric Maven era and avoids the earlier rNN naming era and the oldest migration boundary. Nine earlier numeric tags are outside this study's period.
4. Exclude v13.0 because both v13.0 and v13.0-final appear in the tag inventory; use unambiguous later sampling points. Exclude maintenance releases 23.6.1 and 24.1.1 from mainline sampling because they were published after the newer 25.0 line. All three exclusions are recorded with reasons.
5. Sort the remaining 70 eligible mainline points by release date. Choose index round(i × 69 / 29), for i from 0 through 29. This selects 30 observations across the release history and includes both endpoints. It is uniform in eligible-release rank, not uniform in calendar time.
6. Verify that every adjacent selected pair has at least one omitted numeric stable release between it and the previous observation. Store the actual omitted version names, not just a count.
7. Choose one Maven artifact for each logical release: plain guava versions through 23.0 and the -jre flavor from 23.1 onward. The -android artifact is a platform variant, not an additional temporal observation.

The 82 numeric stable refs become 70 eligible historical mainline points after the 12 explicitly described exclusions. Forty eligible points are deliberately unsampled, leaving 30. No selected release was lost to a missing or corrupt download: all 90 binary/source/POM artifacts were acquired and verified.

Dates through 23.0 come from the project's [ReleaseHistory](https://github.com/google/guava/wiki/ReleaseHistory) and individual release notes, with calendar-day precision. Later dates use GitHub Release.published_at. Git commit timestamps are also retained, but they are not substituted for release publication dates. A lightweight tag has no independent tagger timestamp.

## The selected sample

| # | Guava release | Maven artifact version | Release date (UTC/date only) | Omitted stable tags since previous sample |
|---:|---|---|---|---:|
| 1 | 10.0 | 10.0 | 2011-09-28 | — |
| 2 | 11.0 | 11.0 | 2011-12-18 | 81 |
| 3 | 12.0 | 12.0 | 2012-04-30 | 81 |
| 4 | 13.0.1 | 13.0.1 | 2012-08-28 | 81 |
| 5 | 15.0 | 15.0 | 2013-09-06 | 81 |
| 6 | 16.0.1 | 16.0.1 | 2014-02-03 | 81 |
| 7 | 18.0 | 18.0 | 2014-08-25 | 81 |
| 8 | 21.0 | 21.0 | 2017-01-12 | 81 |
| 9 | 23.0 | 23.0 | 2017-08-04 | 81 |
| 10 | 23.2 | 23.2-jre | 2017-10-11 | 81 |
| 11 | 23.5 | 23.5-jre | 2017-11-22 | 81 |
| 12 | 24.0 | 24.0-jre | 2018-02-01 | 81 |
| 13 | 25.1 | 25.1-jre | 2018-05-31 | 81 |
| 14 | 27.0 | 27.0-jre | 2018-10-18 | 81 |
| 15 | 27.1 | 27.1-jre | 2019-03-08 | 81 |
| 16 | 28.2 | 28.2-jre | 2019-12-27 | 81 |
| 17 | 30.0 | 30.0-jre | 2020-10-16 | 81 |
| 18 | 30.1.1 | 30.1.1-jre | 2021-03-19 | 81 |
| 19 | 31.1 | 31.1-jre | 2022-02-28 | 81 |
| 20 | 32.0.1 | 32.0.1-jre | 2023-06-09 | 81 |
| 21 | 32.1.2 | 32.1.2-jre | 2023-07-31 | 81 |
| 22 | 33.0.0 | 33.0.0-jre | 2023-12-18 | 81 |
| 23 | 33.2.0 | 33.2.0-jre | 2024-05-02 | 81 |
| 24 | 33.3.1 | 33.3.1-jre | 2024-09-23 | 81 |
| 25 | 33.4.1 | 33.4.1-jre | 2025-03-19 | 81 |
| 26 | 33.4.3 | 33.4.3-jre | 2025-03-19 | 81 |
| 27 | 33.4.6 | 33.4.6-jre | 2025-03-25 | 81 |
| 28 | 33.4.8 | 33.4.8-jre | 2025-04-14 | 81 |
| 29 | 33.7.0 | 33.7.0-jre | 2026-08-17 | 81 |
| 30 | 33.7.2 | 33.7.2-jre | 2026-09-29 | 81 |

Full commit SHAs, artifact URLs, SHA-256 pins, Maven SHA-1 pins, and omitted intervening releases are in the manifest. The date source and precision are explicit for each historical entry.

## Scope and interpretation

This study's target is the production Guava JRE artifact, not every module in the repository. Android code, Guava test libraries, benchmarks, GWT artifacts, compatibility artifacts, and external dependencies are outside the input universe. This keeps the implementation variant and production scope consistent over time.

The class universe consists of production classes with source-owned outer classes under com.google.common. The bundled com.google.thirdparty.publicsuffix package is outside that declared boundary, even though its sources are distributed in the Guava repository and JAR. References to JDK classes, failureaccess, and annotation dependencies are external and are removed from the dependency graph.

The public-suffix namespace boundary matters when interpreting changes around 15.0–16.0.1: the earlier com.google.common.net.TrieParser is inside the declared scope, while the later com.google.thirdparty.publicsuffix.TrieParser is outside it. Such a change is partly an analysis-boundary effect and must not be called deletion of functionality from the whole Guava repository.

The phrase "exclude beta versions" applies to prerelease distributions. Guava's @Beta annotation marks an API stability promise within an otherwise stable release; removing all @Beta classes would impose a different, changing API-based scope. The analysis retains these first-party classes.

This is one longitudinal case study. Its results characterize the declared Guava class-dependency graph and the chosen recovery methods; they do not establish universal laws about all Java projects.
