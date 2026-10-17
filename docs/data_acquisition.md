# Data acquisition and provenance (revised study)

## Reproduce the frozen dataset

Run from the repository root:

```bash
python scripts/select_versions.py --check
python scripts/unpack_data.py
python scripts/fetch_data.py --offline --verify-git
```

The selector checks the exact 30-family sample against the frozen tag catalog. Unpacking verifies the stored files, decoded ZIPs and member hashes before restoring the files. The offline acquisition command verifies all pinned artifacts and repeats the endpoint source comparison without network requests. It fails on missing or changed files.

To fetch any missing original Maven artifacts instead:

```bash
python scripts/fetch_data.py
```

The revised collection used `python scripts/fetch_data.py --bootstrap --verify-git`. Bootstrap fills previously absent SHA-256 pins only after validating Maven's published SHA-1 sidecars. It never accepts a different digest for an already pinned artifact. Normal reproduction does not need bootstrap.

## Exactly what was acquired

The [manifest](../config/versions.json) declares one binary JAR, one matching source JAR, and one POM for each of 30 stable releases from 30 distinct major/minor families. Each row records the full immutable Git commit, original tag, Maven coordinates, exact JRE/plain artifact version, URLs, relative paths, SHA-256 values, and published Maven SHA-1 values.

The current sample contains **90 Maven artifacts totaling 121,898,763 bytes (116.252 MiB)**. All selected artifacts are pinned and checked; the calendar revision does not drop a version because of its analysis result. The authoritative run record is [acquisition.json](../data/provenance/acquisition.json), and [SHA256SUMS](../data/provenance/SHA256SUMS) lists all 90 current artifact digests.

The original artifacts are unmodified inputs. Extraction, filtering, clustering, and evaluation write separate derived outputs. Committed per-version archives restore the `data/raw/VERSION` paths; caches for an older study may remain on a working machine but are not additional observations in the current manifest. Version and pilot ZIPs are stored as `.zip.b64` text, decoded automatically by the same unpack command. The stored-text and decoded-ZIP checksums establish that the original ZIP bytes are preserved. [Archive format](../archives/README.md)

Example for the last sampled release:

```text
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre.jar
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre-sources.jar
https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre.pom
```

The downloader uses four concurrent workers by default, standard-library HTTPS, bounded retries, and a response-size limit. It does not build or execute Guava. POM validation follows an inherited version from `guava-parent` if the child POM does not repeat it.

## What the checks establish

Each JAR is checked as a ZIP archive, including member CRCs. The computed SHA-1 is checked against Maven Central's published sidecar during initial collection. The observed SHA-256 is pinned, and every later run checks it. POM identity must match the declared artifact and version.

These checks establish exactly which bytes were analyzed and detect changes or corruption. A checksum served by the same host is not an independent signature or proof of authorship; no PGP signature verification is claimed.

The GitHub tag names are pinned to immutable commits. At the two study endpoints, every Java file in the Maven source JAR was compared with its corresponding file in the pinned Git commit ZIP:

| Endpoint | Pinned commit | Java files checked | Result |
|---|---|---:|---|
| 10.0 | baf008c5a3de60e8399852f23979bf69f2660023 | 326 | All byte-identical |
| 33.7.2 | 666338cc49d5686c07e3e4d17f0aa1cec25a2be6 | 611 | All byte-identical |

The detailed comparisons are [git_source_match_10.0.json](../data/provenance/git_source_match_10.0.json) and [git_source_match_33.7.2.json](../data/provenance/git_source_match_33.7.2.json). Source JAR hashes exist for all 30 releases. A byte-for-byte source-to-Git comparison is claimed for these two endpoints only.

The pinned Git source ZIPs are restored under `data/upstream_git` by the committed archive package, enabling an offline repeat of these checks. Their URLs and hashes are also recorded in the comparison files.

## Source ownership and counts

The revised ownership scope includes source paths under both `com/google/common/` and `com/google/thirdparty/publicsuffix/`. The latter is Guava's own Java implementation, as established by its distributed source and Guava Authors headers. A namespace containing the word `thirdparty` does not automatically make every class in it an external dependency.

The last sampled source JAR has the following inventory:

| Source scope | Java files | Nonblank, noncomment physical Java lines |
|---|---:|---:|
| `com.google.common` | 607 | 95,876 |
| `com.google.thirdparty.publicsuffix` | 3 | 746 |
| Combined project-owned source scope | **610** | **96,622** |
| Complete source JAR, including module descriptor | 611 | 96,646 |

The complete binary JAR has 1,965 base `.class` entries, of which 1,948 have source-owned outer classes under the combined prefixes before merging. These raw counts include compiler-created inner/anonymous classes and differ from final architecture node counts. Descriptor files and annotation policy can affect retained graph counts. The extractor's detailed cleaning audit is authoritative for the actual node and edge universe.

The source-line counter preserves quoted strings and character literals while removing line and block comments, then counts nonempty remaining lines. It measures physical lines, not logical statements. Source-owned totals include package descriptors under the two prefixes. Java source file counts are not equivalent to merged class-node counts.

All external endpoints remain excluded: JDK, failureaccess, external annotation libraries, and other dependencies do not become architecture nodes. The instructor extractor is the revised class-relationship baseline; supplemental member evidence supports UE. Those decisions and their limits are explained in [modeling_decisions.md](modeling_decisions.md).

## Explain it in the oral exam

A concise account is:

> We selected 30 distinct Guava major/minor families from a frozen public tag catalog. We covered all 24 major versions, retained the latest endpoint and selected five additional minor releases to reduce long calendar gaps, subject to minimum spacing and a cap on additions per major. Each family contributed one release. We recorded each tag's commit SHA and downloaded its released binary JAR, source JAR, and POM from Maven Central. We checked the published SHA-1 values, pinned SHA-256 values, and compared every Java source file at the oldest and latest endpoints with the immutable Git commits. Source ownership includes Guava's common packages and its own public-suffix implementation. We then used the instructor's dependency extractor and a documented cleanup policy, removed external endpoints, merged inner classes into their outer owners, and analyzed the internal graph. The member-level extractor supplies the separate evidence required by the UE equations.

Be ready to distinguish a family representative from repeated patch observations, a release from a JRE/Android flavor, a source file from a bytecode class entry, a tag name from a commit SHA, checksum verification from signature verification, and acquisition evidence from architectural interpretation.
