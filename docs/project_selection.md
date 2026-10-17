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

The original release-rank sample gave several observations to heavily patched families. The second sample avoided repeated families, but family spacing still placed four 23.x releases within 56 days. Distinct version labels therefore did not guarantee useful separation in time.

The current sample covers every major version and uses elapsed time to place its additional minor releases. This is a response to the requested sporadic sampling. It does not choose or discard releases by their class counts, graph differences, clustering results or MQ. Identical graphs, if observed, remain valid evidence of structural stability.

## Reproducible selection rule

[scripts/select_versions.py](../scripts/select_versions.py) reads the captured release catalog only.

1. Start with the tag snapshot captured on **2026-10-17**: 124 tag references, of which 82 match numeric stable-release names. The other 42 include prereleases, auxiliary-component tags and alternative names; they are not all beta releases.
2. Begin the sampling window at 10.0, excluding nine earlier numeric tags. Retain the documented exclusions for the ambiguous `v13.0`/`v13.0-final` naming and the later 23.6.1/24.1.1 backports to older lines. There are **70 eligible mainline releases in 45 major/minor families**.
3. Select the first eligible `.0` release of every major version from 10 through 33. These **24 anchors** cover all major lines. Major 13 uses **13.0.1** because the 13.0 tags are excluded.
4. Add the latest eligible release, **33.7.2**, as the endpoint. This is the sole latest-patch exception to using first-eligible representatives.
5. Fill the remaining **five places** from the first eligible releases of unused minor families. For each candidate, let L and R be its distances in days from the nearest selected releases before and after it. Adding it reduces the sum of squared calendar gaps by `(L+R)^2-L^2-R^2 = 2LR`. Choose the candidate with the largest reduction, provided every resulting interval is at least **60 days** and no major receives more than **two optional additions**. Resolve ties by earlier publication date, then lower numeric version. Repeat until 30 releases are selected.
6. Use the plain Guava artifact before 23.1 and the JRE artifact after the platform split. Android variants do not add observations. Verify the exact cohort, distinct families, tag/commit identities, release dates, minimum gap and per-major addition cap.

The five optional additions, in selection order, are **33.5.0, 33.4.0, 31.1, 28.2 and 27.1**. The final chronological gaps range from **74 to 471 days**, with median **141 days**. All 24 majors are represented; all 30 families are distinct. The cap applies to the five optional additions: major 33 has its anchor, the fixed latest endpoint and two optional minors, for four observations in total.

This is not uniform calendar sampling, and it does not ban adjacent numeric minor labels. For example, **33.4.0 and 33.5.0 are 275 days apart**. The major anchors guarantee historical coverage, while the additional minors reduce long gaps without concentrating every remaining place in the latest major. The 60-day threshold, per-major cap and squared-gap objective are declared study choices; the course does not prescribe this exact algorithm.

The full candidate catalog, chosen roles, intermediate gap reductions and skipped releases are recorded in [family_selection.json](../data/provenance/family_selection.json) and [config/versions.json](../config/versions.json). Fifteen of the 45 families are unselected, and 40 eligible individual releases are outside the final sample.

To verify the saved cohort without changing it:

```bash
python scripts/select_versions.py --check
```

To recreate it from the same catalog while preserving existing artifact checksum pins:

```bash
python scripts/select_versions.py --write
```

These commands do not refresh the public catalog. A later cutoff or a different sampling policy defines a new study configuration.

## The selected sample

| # | Release | Family | Maven artifact | Published | Selection role |
|---:|---|---|---|---|---|
| 1 | 10.0 | 10.0 | 10.0 | 2011-09-28 | Major anchor |
| 2 | 11.0 | 11.0 | 11.0 | 2011-12-18 | Major anchor |
| 3 | 12.0 | 12.0 | 12.0 | 2012-04-30 | Major anchor |
| 4 | 13.0.1 | 13.0 | 13.0.1 | 2012-08-28 | Major anchor |
| 5 | 14.0 | 14.0 | 14.0 | 2013-02-25 | Major anchor |
| 6 | 15.0 | 15.0 | 15.0 | 2013-09-06 | Major anchor |
| 7 | 16.0 | 16.0 | 16.0 | 2014-01-17 | Major anchor |
| 8 | 17.0 | 17.0 | 17.0 | 2014-04-22 | Major anchor |
| 9 | 18.0 | 18.0 | 18.0 | 2014-08-25 | Major anchor |
| 10 | 19.0 | 19.0 | 19.0 | 2015-12-09 | Major anchor |
| 11 | 20.0 | 20.0 | 20.0 | 2016-10-28 | Major anchor |
| 12 | 21.0 | 21.0 | 21.0 | 2017-01-12 | Major anchor |
| 13 | 22.0 | 22.0 | 22.0 | 2017-05-22 | Major anchor |
| 14 | 23.0 | 23.0 | 23.0 | 2017-08-04 | Major anchor |
| 15 | 24.0 | 24.0 | 24.0-jre | 2018-02-01 | Major anchor |
| 16 | 25.0 | 25.0 | 25.0-jre | 2018-04-25 | Major anchor |
| 17 | 26.0 | 26.0 | 26.0-jre | 2018-08-01 | Major anchor |
| 18 | 27.0 | 27.0 | 27.0-jre | 2018-10-18 | Major anchor |
| 19 | 27.1 | 27.1 | 27.1-jre | 2019-03-08 | Minor gap fill |
| 20 | 28.0 | 28.0 | 28.0-jre | 2019-06-12 | Major anchor |
| 21 | 28.2 | 28.2 | 28.2-jre | 2019-12-27 | Minor gap fill |
| 22 | 29.0 | 29.0 | 29.0-jre | 2020-04-13 | Major anchor |
| 23 | 30.0 | 30.0 | 30.0-jre | 2020-10-16 | Major anchor |
| 24 | 31.0 | 31.0 | 31.0-jre | 2021-09-24 | Major anchor |
| 25 | 31.1 | 31.1 | 31.1-jre | 2022-02-28 | Minor gap fill |
| 26 | 32.0.0 | 32.0 | 32.0.0-jre | 2023-05-29 | Major anchor |
| 27 | 33.0.0 | 33.0 | 33.0.0-jre | 2023-12-18 | Major anchor |
| 28 | 33.4.0 | 33.4 | 33.4.0-jre | 2024-12-16 | Minor gap fill |
| 29 | 33.5.0 | 33.5 | 33.5.0-jre | 2025-09-17 | Minor gap fill |
| 30 | 33.7.2 | 33.7 | 33.7.2-jre | 2026-09-29 | Latest endpoint |

The manifest stores the full commit SHA, tag, artifact URLs, SHA-256 and Maven SHA-1 pins, skipped stable release names, and omitted family names. Dates through 23.0 are calendar dates from the project's [ReleaseHistory](https://github.com/google/guava/wiki/ReleaseHistory) and individual release notes; later dates use `GitHub Release.published_at`. Git commit timestamps are retained separately. A lightweight tag has no independent tagger timestamp.

## Project ownership and external dependencies

The input scope is the **production Guava JRE artifact**, not every module in the Git repository. Android, GWT, test libraries, benchmarks, and separately published compatibility artifacts are outside the target variant.

Project-owned production sources under both `com.google.common` and `com.google.thirdparty.publicsuffix` are included. The public-suffix Java implementation is distributed as Guava source and carries Guava Authors copyright headers. Its package name is not evidence that it is an external library. The provenance of public-suffix list data is a separate question from ownership of the Java implementation using that data.

The earlier namespace-only study excluded this support package. Including it avoids treating a move from `com.google.common.net.TrieParser` to `com.google.thirdparty.publicsuffix.TrieParser` as loss of functionality from Guava. The study still cannot automatically identify every rename across versions; class identity is based on canonical names.

JDK classes, failureaccess, external annotation libraries, and other external endpoints are excluded. A dependency is retained only when both endpoints belong to the retained project class universe. Instructor extraction and the annotation policy are specified separately in [modeling_decisions.md](modeling_decisions.md); this document defines artifact and source ownership, not which relationship kinds a tool can observe.

“Exclude beta versions” refers to prerelease distributions. The presence of Guava's `@Beta` annotation on a class within a stable release does not remove that first-party class from the study.

This is one longitudinal case study of a declared artifact, scope, and measurement process. Its results do not establish universal software-evolution laws.
