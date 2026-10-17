# Original ACDC provenance

The unmodified archive `acdc.tar` was downloaded directly from its author's York
University host:

https://www.eecs.yorku.ca/~bil/downloads/acdc.tar

The assignment links the algorithm page:

https://wiki.eecs.yorku.ca/project/cluster/protected:acdc

- Archive size: 163,840 bytes.
- Archive SHA-256: `52755a6889a3f3f93cfe83f0a54639d62925442b54f8638f0dbd9d9ebdaf749c`.
- Actual retrieval time and URL: `download.json`.
- Original archive contents: upstream `README`, 18 `.java` sources and their
  supplied compiled `.class` files under `acdc/`.
- Locally compiled classes are produced separately under `build/acdc`.
- The original Java source has not been replaced with a locally invented
  approximation or the modified ARCADE implementation.

The Python adapter executes `acdc.ACDC`, selects `+so`, passes `-l20`, requests
progress logs, and retains the default fine-grained flat output. The maximum-size
option constrains SubGraph construction; the upstream final orphan container is
not silently split. Genuine graph isolates, absent from dependency-only RSF input,
are recorded and restored as singleton analysis clusters by the adapter.

Attribution: Vassilios Tzerpos and Richard C. Holt, “ACDC: An Algorithm for
Comprehension-Driven Clustering,” WCRE 2000, pp. 258–267,
https://doi.org/10.1109/WCRE.2000.891477.

The upstream archive does not include a separate license file. Its original
attribution and contents are retained; any license covering this study's new code
does not purport to relicense the upstream implementation.
