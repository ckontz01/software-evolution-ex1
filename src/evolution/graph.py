"""Validated, scoped graph inputs and deterministic audit-file helpers."""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


@dataclass(frozen=True)
class Graph:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]

    def __post_init__(self):
        if len(self.nodes) != len(set(self.nodes)):
            raise ValueError("Duplicate graph nodes")
        if len(self.edges) != len(set(self.edges)):
            raise ValueError("Duplicate graph edges: expected binary graph")
        nodes = set(self.nodes)
        if any(a not in nodes or b not in nodes or a == b for a, b in self.edges):
            raise ValueError("Out-of-scope endpoint or self loop")

    @property
    def isolates(self) -> tuple[str, ...]:
        active = {v for edge in self.edges for v in edge}
        return tuple(n for n in self.nodes if n not in active)

    def without(self, removed) -> "Graph":
        removed = set(removed)
        if not removed <= set(self.nodes):
            raise ValueError("Attempt to remove nonexistent graph nodes")
        return Graph(tuple(n for n in self.nodes if n not in removed),
                     tuple((a, b) for a, b in self.edges if a not in removed and b not in removed))

    def rsf(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(f"call {a} {b}\n" for a, b in self.edges))


def read_graph(directory: Path) -> Graph:
    nodes = tuple(row["class"] for row in read_csv(directory / "classes.csv"))
    edges = tuple((row["source"], row["target"]) for row in read_csv(directory / "dependencies.csv"))
    return Graph(nodes, edges)
