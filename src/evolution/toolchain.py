"""Small portable Java toolchain wrapper; target application classes are never executed."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TOOLS = {
    "asm-9.7.1.jar": "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281",
    "ecj-3.37.0.jar": "cde026ff966b48b5e5f148b6f041ceff3cf4f85cf75155f4ec0f40e4ee14b545",
}


def java_path(explicit: str | None = None) -> str:
    value = explicit or os.environ.get("EVOLUTION_JAVA")
    local = ROOT / "config/toolchain.local.json"
    if not value and local.exists():
        value = json.loads(local.read_text())["java"]
    value = value or shutil.which("java")
    if not value:
        raise RuntimeError("Install Java 17+ or set EVOLUTION_JAVA to its java executable")
    return str(Path(value).resolve())


def java_env(java: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    home = Path(java_path(java)).parent.parent
    libs = [str(p) for p in (home / "lib", home / "lib/server") if p.is_dir()]
    if libs:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(libs + ([env["LD_LIBRARY_PATH"]] if env.get("LD_LIBRARY_PATH") else []))
    return env


def verify_tools() -> None:
    for name, expected in TOOLS.items():
        path = ROOT / "tools" / name
        if not path.exists():
            raise RuntimeError(f"Missing {path}; run python scripts/fetch_tools.py")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Tool checksum mismatch: {name}")


def build_java(java: str | None = None) -> dict:
    verify_tools()
    executable = java_path(java)
    env = java_env(executable)
    version = subprocess.run([executable, "-version"], check=True, capture_output=True, text=True, env=env)
    ecj = str(ROOT / "tools/ecj-3.37.0.jar")
    commands = []
    for name, release, sources, extra in [
        ("extractor", "-17", [ROOT / "java/DependencyExtractor.java"], ["-cp", str(ROOT / "tools/asm-9.7.1.jar")]),
        ("acdc", "-8", sorted((ROOT / "third_party/acdc/acdc").glob("*.java")), []),
    ]:
        out = ROOT / "build" / name
        out.mkdir(parents=True, exist_ok=True)
        if not sources:
            raise RuntimeError(f"No {name} sources found")
        command = [executable, "-jar", ecj, release, "-nowarn", *extra, "-d", str(out), *map(str, sources)]
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        commands.append({"component": name, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"Java compilation failed for {name}: {result.stdout}\n{result.stderr}")
    details = {"java_version": (version.stderr + version.stdout).strip(), "compiler": "Eclipse ECJ 3.37.0", "asm": "9.7.1", "builds": commands}
    (ROOT / "build/toolchain.json").write_text(json.dumps(details, indent=2) + "\n")
    return details
