# Instructor-provided DependencyExtractor

`DependencyExtractor.jar` is the **unmodified instructor-provided binary** from
the EPL484 Project 1 attachment `DependencyExtractor (1).jar`. The later uploaded
`DependencyExtractor (2).jar` had the same bytes. No public distribution URL or
separate license statement was supplied with the attachment; this file records
its supplied provenance and does not assert a new license for the upstream tool.
Original notices and nested dependency files remain in the original archive.

SHA-256:
`8e4e857222dba569cc48ddf2bc58d3ac206d4ee1c0d5228b7b69517016450e9c`

`source.json` records the original JAR size, hash and hashes of its four bundled
dependency JARs. Those dependencies support analysis; they are never included as
target Guava nodes.

## Portable launcher

The supplied Eclipse jar-in-jar launcher could not locate ASM on the recorded
Java 17 runtime. `evolution.toolchain.instructor_classpath()` verifies the
original JAR and extracts its unchanged `ant-1.6.5.jar`, `javaparser-1.0.8.jar`,
`ant.jar`, and `asm-9.7.1.jar` into ignored `build/instructor-libs`. The pipeline
then directly starts the original `CompCalc.MainClass` using an explicit Java
classpath. Neither the extractor implementation nor the bundled dependency
implementations are patched. Target Guava classes are read as bytes, and are
never added to the JVM executable classpath.

`python scripts/fetch_tools.py` prepares and verifies the launcher offline when
the already bundled tool files are present. Each release preserves its exact
invocation in `instructor_command.json`, console output in `instructor.log`,
and the original tool-generated CSV in `instructor_raw.csv`.

## Role in the revised study

The instructor tool is the **sole source of primary graph relationships**. Its
raw seven-category relationships are normalized by the independently recorded
class aliases; both endpoints must be source-owned, and merging-generated
self-loops and duplicate pairs are removed. Occurrence counts (`Times`) are
preserved in the raw file and are not used as graph weights.

A deterministic `instructor_input.jar` contains only owned base class entries
from the original binary. Each retained class byte array is unchanged; entry
hashes and input-artifact hashes are recorded. Multi-release override entries,
module/package descriptors, and unowned binary entries are excluded. The full
original Maven artifact is preserved separately.

The custom `java/DependencyExtractor.java` now has a supplemental role: source
ownership, outermost class mapping, declaration-resolved field/method member
evidence for Usage Equality, and an explicitly separate broad graph for the
extractor sensitivity audit. Its `supplemental_dependencies*.csv` files do not
contribute any extra relationship to the primary graph. Annotation applications
therefore cannot be silently added by the supplemental pass. Owned annotation
type nodes and any ordinary code references recorded by the instructor remain.
