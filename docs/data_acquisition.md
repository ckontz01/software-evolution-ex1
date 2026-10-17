# Data acquisition and provenance

## Reproduce the dataset

Run from the repository root:

```bash
python scripts/fetch_data.py
python scripts/fetch_data.py --offline
```

The first command downloads any missing public Maven artifacts and checks them against the SHA-256 values already pinned in config/versions.json. The second command makes no network requests and verifies the checked-in copies. It fails on missing or changed files rather than accepting a replacement.

The one-time initial collection used:

```bash
python scripts/fetch_data.py --bootstrap --verify-git
```

The bootstrap option fills previously absent checksum pins after validating the Maven-published SHA-1 sidecars. It never replaces an existing SHA-256 pin with a different digest. Normal reproduction does not need bootstrap.

## Exactly what was downloaded

For each of the 30 logical releases, the manifest declares:

- The full Git commit SHA and the original tag name.
- The Maven group com.google.guava, artifact guava, and exact platform-specific artifact version.
- One compiled production JAR for dependency extraction.
- One corresponding source JAR for class ownership and source inspection.
- One POM for artifact identity, dependencies, and build provenance.
- The download URLs, local relative paths, SHA-256 digests, and published Maven SHA-1 digests.

All 90 release artifacts are available under data/raw and total 122.018 MiB. Binary files remain unmodified; cleaned dependency graphs and clusters are derived outputs stored separately by the analysis pipeline.

Example for the latest version:

```text
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre.jar
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre-sources.jar
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre.pom
```

The downloader uses four concurrent workers by default and standard-library HTTPS, with bounded retries. It does not build or execute Guava. POM validation follows an inherited version from guava-parent when the child POM does not repeat it.

## What the checks establish

Every downloaded JAR is checked as a ZIP archive, including member CRCs. The computed SHA-1 is checked against Maven Central's published sidecar during initial collection. SHA-256 is then pinned for repeatability. Every subsequent online or offline run checks the pinned SHA-256.

These checks identify the exact analyzed bytes and detect later changes or corruption. A same-server checksum is not an independent signature or proof of authorship; no PGP signature verification is claimed.

The GitHub lightweight tag refs are pinned to immutable commits. At both study endpoints, every Java file in the Maven source JAR was compared byte-for-byte with the corresponding source at that commit:

| Endpoint | Pinned commit | Java files checked | Result |
|---|---|---:|---|
| 10.0 | baf008c5a3de60e8399852f23979bf69f2660023 | 326 | All byte-identical |
| 33.7.2 | 666338cc49d5686c07e3e4d17f0aa1cec25a2be6 | 611 | All byte-identical |

The detailed comparisons are [git_source_match_10.0.json](../data/provenance/git_source_match_10.0.json) and [git_source_match_33.7.2.json](../data/provenance/git_source_match_33.7.2.json). The input source archives have pinned SHA-256 values for all 30 releases; byte-for-byte source-to-Git comparison was performed for the two endpoints, not claimed for every intermediate release.

To repeat those endpoint comparisons online:

```bash
python scripts/fetch_data.py --verify-git
```

Git source ZIPs are temporary cache inputs under data/upstream_git. Their immutable URLs and observed digests are recorded in the comparison files; the much smaller per-file evidence remains in the repository.

## Counts and class ownership

The latest source JAR has 611 Java files. Of these, 607 are under com.google.common, containing 95,876 nonblank, noncomment physical Java lines. The full source JAR has 96,646 such lines. The difference consists of the public-suffix support and module descriptor outside the declared analysis scope.

The source-line counter preserves quoted string and character literals while removing line and block comments, then counts nonempty remaining lines. It measures physical source lines, not logical statements. It includes package descriptors under the selected package prefix. Source file counts are not merged architecture class counts.

The base latest binary JAR contains 1,965 class entries. There are 1,944 entries with source-owned outer classes under com.google.common before merging inner and anonymous classes. These raw figures include compiler-generated inner classes and differ from the graph's final node count. The extractor's cleaning audit is the authoritative account of merged nodes, discarded descriptors, external endpoints, self-edges, and duplicate edges.

Source JAR ownership is important: a third-party class can be bundled inside a project JAR. The library itself also references JDK and other dependency types which must not become architecture nodes. The pipeline retains a dependency only when both endpoints are retained project classes.

## Oral-exam explanation

A concise account is: "We selected 30 spaced, stable Guava JRE releases from a frozen public tag catalog. We recorded each tag's commit SHA and downloaded its released binary JAR, source JAR, and POM from Maven Central. We checked published SHA-1 values, pinned SHA-256 values, and compared every source Java file at the oldest and latest endpoints with the immutable Git commits. We used the source JAR to define project-owned classes, filtered external dependencies, merged compiler-created inner/anonymous classes into their outer classes, and analyzed the resulting internal graph. The manifest and provenance files allow someone else to obtain the same bytes and check our scope decisions."

Be ready to distinguish a release from a platform variant, a Java source file from a bytecode class entry, a tag name from an immutable commit SHA, and a checksum identity check from signature verification.
