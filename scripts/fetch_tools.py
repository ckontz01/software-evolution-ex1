#!/usr/bin/env python3
"""Verify pinned tools, fetching public ASM/ECJ only when absent.

The instructor JAR is bundled unchanged and its nested analysis dependencies
are extracted locally for the portable classpath launcher. These libraries are
analysis tools; they never become nodes in the target Guava graph.
"""
from pathlib import Path
import hashlib
import urllib.request
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evolution.toolchain import instructor_classpath
ARTIFACTS = [
    ("asm-9.7.1.jar", "org/ow2/asm/asm/9.7.1/asm-9.7.1.jar", "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281"),
    ("ecj-3.37.0.jar", "org/eclipse/jdt/ecj/3.37.0/ecj-3.37.0.jar", "cde026ff966b48b5e5f148b6f041ceff3cf4f85cf75155f4ec0f40e4ee14b545"),
]

if __name__ == "__main__":
    (ROOT / "tools").mkdir(exist_ok=True)
    for filename, suffix, expected in ARTIFACTS:
        target = ROOT / "tools" / filename
        if not target.exists():
            with urllib.request.urlopen("https://repo.maven.apache.org/maven2/" + suffix, timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f"Checksum mismatch: {filename}")
            target.write_bytes(content)
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {filename}")
        print("verified", filename)
    for path in instructor_classpath():
        print("verified", path.relative_to(ROOT).as_posix())
