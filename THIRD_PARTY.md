# Upstream software and attribution

This study analyzes the official **Google Guava** JRE artifacts under the Apache License2.0. The unmodified binary and matching source JARs, including their upstream license/notice entries, are preserved inside the version archives. Provenance, Maven URLs and SHA256 hashes are in `config/versions.json` and `data/provenance/`. The study's internal-only analysis boundary does not change the distribution's license or ownership.

The original **ACDC** implementation is from the York University clustering project. Its archive and source are preserved unmodified in `third_party/acdc/`; see `UPSTREAM.md` there for attribution, exact source URL and checksum. No license for that research distribution is invented or replaced here. Our adapter maps identifiers and restores isolates around the original process.

**ASM9.7.1** (OW2, BSD3-clause) reads Java bytecode. **Eclipse ECJ3.37.0** (Eclipse JDT, EPL2.0) compiles the extractor and original ACDC. Their exact Maven URLs/hashes are fixed by `scripts/fetch_tools.py`; the JARs are also supplied for reproducibility. These are analysis-tool dependencies; none is a node in the Guava dependency graphs.

Python numerical/plotting/PDF packages are pinned in `requirements.txt`; their installed versions are recorded in `results/run_manifest.json`. They likewise are analysis dependencies, not subjects of the class analysis.

The course PDFs and attached scholarly paper are referenced by title and page in the report and course traceability document. They are not redistributed as repository attachments. The supplied incorrect JNode and older extractor are not used as black-box implementations of this study.
