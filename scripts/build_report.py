#!/usr/bin/env python3
"""Build the Guava report and figures exclusively from saved experiment data.

Run after ``python scripts/run_study.py --phase all``. This program never runs a
new clustering experiment, changes a partition, or fills in missing measurements.
The PDF skill's session marker is an authoring-environment operation, not a
dependency of this independently reproducible script.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import html
import importlib.metadata
import json
import math
import re
import shutil
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "results/figures"
REPORT = ROOT / "report"
PAGE_W, PAGE_H = A4
MARGIN = 49
WIDTH = PAGE_W - 2 * MARGIN
NAVY = "#172F40"
TEAL = "#247D72"
OCHRE = "#B2662F"
MUTED = "#536470"
PALE = "#EDF3F3"
CONDITIONS = ("A1", "A2", "A3", "A4")
CONDITION_LABELS = {
    "A1": "ACDC · full", "A2": "ACDC · UE filtered",
    "A3": "KMeans · full", "A4": "KMeans · UE filtered",
}
LINE_STYLES = {
    "A1": dict(color="#235C7E", linestyle="-", marker="o"),
    "A2": dict(color="#428DAB", linestyle="--", marker="s"),
    "A3": dict(color="#B45D28", linestyle="-", marker="^"),
    "A4": dict(color="#DA9953", linestyle="--", marker="D"),
}
READ_INPUTS: set[Path] = set()


def read_json(path):
    path = Path(path).resolve()
    READ_INPUTS.add(path)
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    path = Path(path).resolve()
    READ_INPUTS.add(path)
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(row, key):
    value = row[key]
    if value in (None, "", "None"):
        return math.nan
    return float(value)


def integer(row, key):
    value = number(row, key)
    if not math.isfinite(value) or value != int(value):
        raise ValueError(f"Expected an integer in {key}: {row}")
    return int(value)


def fmt(value, decimals=3):
    if value is None:
        return "—"
    value = float(value)
    return f"{value:.{decimals}f}" if math.isfinite(value) else "—"


def count(value):
    return f"{int(value):,}"


def percent(value, decimals=1):
    return f"{100 * float(value):.{decimals}f}%"


def esc(value):
    return html.escape(str(value))


def short_class(name):
    return str(name).removeprefix("com.google.common.")


def excerpt(text, limit=160):
    """Display an explicitly labeled excerpt; preserve full text in its artifact."""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


class StudyData:
    """Strictly validate the measurement/manifest join before publishing results."""

    def __init__(self):
        required = ["sizes.csv", "metrics.csv", "same_graph_comparisons.csv",
                    "evolution.csv", "runtimes.csv", "run_manifest.json", "partition_comparisons.csv"]
        absent = [str(Path("results") / f) for f in required if not (ROOT / "results" / f).exists()]
        if absent:
            raise FileNotFoundError("Run the complete study before the report; missing: " + ", ".join(absent))
        self.manifest = read_json(ROOT / "config/versions.json")
        self.config = read_json(ROOT / "config/analysis.json")
        self.run = read_json(ROOT / "results/run_manifest.json")
        self.versions = self.manifest["versions"]
        self.names = [v["version"] for v in self.versions]
        self.sizes = read_csv(ROOT / "results/sizes.csv")
        self.metrics = read_csv(ROOT / "results/metrics.csv")
        self.same_graph = read_csv(ROOT / "results/same_graph_comparisons.csv")
        self.evolution = read_csv(ROOT / "results/evolution.csv")
        self.runtimes = read_csv(ROOT / "results/runtimes.csv")
        self.partition_comparisons = read_csv(ROOT / "results/partition_comparisons.csv")
        if len(self.partition_comparisons) != 178:
            raise ValueError("Expected 178 classical same-universe directional comparison pairs")
        if [r["version"] for r in self.sizes] != self.names or len(self.names) != 30:
            raise ValueError("The size table must match all 30 manifest releases in order")
        if len(self.metrics) != 120 or {(r["version"], r["condition"]) for r in self.metrics} != {
            (v, c) for v in self.names for c in CONDITIONS
        }:
            raise ValueError("Expected exactly one final measurement for each of 30 × 4 conditions")
        if (len(self.same_graph), len(self.evolution), len(self.runtimes)) != (60, 29, 180):
            raise ValueError("Incomplete same-graph, evolution or runtime results")
        for filename, key in (("versions.json", "manifest_sha256"), ("analysis.json", "config_sha256")):
            if self.run[key] != sha256(ROOT / "config" / filename):
                raise ValueError(f"Study was generated from different {filename}; rerun the study")
        self.by_version = {r["version"]: r for r in self.sizes}
        self.by_metric = {(r["version"], r["condition"]): r for r in self.metrics}
        self.series = {c: [self.by_metric[v, c] for v in self.names] for c in CONDITIONS}
        for row in self.metrics:
            size = self.by_version[row["version"]]
            filtered = row["condition"] in ("A2", "A4")
            expected_n = integer(size, "retained_classes" if filtered else "classes")
            expected_e = integer(size, "retained_dependencies" if filtered else "dependencies")
            if (integer(row, "n_nodes"), integer(row, "n_edges")) != (expected_n, expected_e):
                raise ValueError("Metric row is evaluated on the wrong graph")
            if not math.isclose(number(row, "cohesion") - number(row, "coupling"),
                                number(row, "mq"), abs_tol=1e-12):
                raise ValueError("MQ differs from the documented lecture formula")
        self.eligibility = read_json(ROOT / "data/provenance/project_eligibility.json")
        self.acquisition = read_json(ROOT / "data/provenance/acquisition.json")
        self.catalog = read_json(ROOT / "data/provenance/tag_inventory.json")
        self.family_selection = read_json(ROOT / "data/provenance/family_selection.json")
        self.baseline_sizes = read_csv(ROOT / "results/baseline_v1/sizes.csv")
        self.baseline_metrics = read_csv(ROOT / "results/baseline_v1/metrics.csv")
        self.graph_provenance = {v: read_json(ROOT / "data/graphs" / v / "provenance.json") for v in self.names}
        if any("instructor" not in item.get("primary_extractor", "").lower() for item in self.graph_provenance.values()):
            raise ValueError("The revised report requires instructor-derived graphs for all 30 releases")
        self.class_breakdown = []
        for v in self.names:
            classes = read_csv(ROOT / "data/graphs" / v / "classes.csv")
            edges = read_csv(ROOT / "data/graphs" / v / "dependencies.csv")
            annotations = {r["class"] for r in classes if r["kind"] == "annotation"}
            touched = {r[k] for r in edges for k in ("source", "target")}
            isolates = {r["class"] for r in classes} - touched
            self.class_breakdown.append({"version": v, "classes": len(classes),
                "annotations": len(annotations), "non_annotations": len(classes) - len(annotations),
                "isolates": len(isolates), "annotation_isolates": len(annotations & isolates)})
        self.pilot = read_json(ROOT / "results/pilot/pilot.json")
        self.calibration = read_json(ROOT / "results/pilot/k_calibration.json")
        if self.run["k_calibration_sha256"] != sha256(ROOT / "results/pilot/k_calibration.json"):
            raise ValueError("The reported pilot calibration differs from the final run")
        self.benchmark = read_json(ROOT / "results/performance/ue_benchmark.json")
        self.ue_cases = read_json(ROOT / "results/performance/case_checks.json")
        if not self.ue_cases["all_checks_passed"]:
            raise ValueError("Independent UE case audit did not pass")
        self.changes = read_json(ROOT / "results/change_points.json")
        if self.changes["status"] != "passed" or self.changes["versions_manifest_sha256"] != self.run["manifest_sha256"]:
            raise ValueError("Change-point audit is incomplete or refers to a different selection")
        self.ue = {v: read_json(ROOT / "results/versions" / v / "ue.json") for v in self.names}
        self.removal_frequency = Counter(n for r in self.ue.values() for n in r["removed_classes"])
        self.first, self.last = self.sizes[0], self.sizes[-1]
        self.latest = self.names[-1]
        self.ai_dir = ROOT / "results/ai"
        self.inputs = [ROOT / "config/versions.json", ROOT / "config/analysis.json"]
        self.inputs.extend(ROOT / "results" / f for f in required)
        self.inputs.extend([ROOT / "results/pilot/pilot.json", ROOT / "results/performance/ue_benchmark.json"])

    def metric(self, condition, key, version=None):
        return number(self.by_metric[version or self.latest, condition], key)

    def comparison(self, full):
        return [r for r in self.same_graph if r["full_condition"] == full]

    def latest_partition(self, condition):
        return read_csv(ROOT / "results/versions" / self.latest / f"{condition}.csv")


def setup_fonts():
    # Matplotlib bundles the complete DejaVu family, including italics. Reusing
    # its pinned dependency avoids a platform-specific system-font requirement.
    font_root = Path(matplotlib.get_data_path()) / "fonts/ttf"
    names = {"Body": "DejaVuSans.ttf", "Body-Bold": "DejaVuSans-Bold.ttf",
             "Body-Italic": "DejaVuSans-Oblique.ttf", "Mono": "DejaVuSansMono.ttf",
             "Title": "DejaVuSerif.ttf", "Title-Bold": "DejaVuSerif-Bold.ttf"}
    for name, filename in names.items():
        path = font_root / filename
        if not path.exists():
            raise FileNotFoundError(f"Matplotlib's bundled DejaVu font is missing: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-Bold")
    pdfmetrics.registerFontFamily("Title", normal="Title", bold="Title-Bold", italic="Title", boldItalic="Title-Bold")


def configure_plots():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11,
        "axes.labelsize": 9, "axes.labelcolor": MUTED, "text.color": NAVY,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "axes.grid": True, "grid.color": "#DCE4E5", "grid.alpha": 0.8,
        "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "svg.hashsalt": "guava-evolution-ex1",
    })


def sample_ticks(ax, data, every=3):
    indexes = sorted(set(range(0, len(data.names), every)) | {len(data.names) - 1})
    ax.set_xticks(indexes, [data.names[i] for i in indexes], rotation=40, ha="right")
    ax.set_xlim(-0.5, len(data.names) - 0.5)
    ax.set_xlabel("Selected stable release (ordered, irregular calendar intervals)")


def condition_lines(ax, data, key):
    x = range(len(data.names))
    for condition in CONDITIONS:
        ax.plot(x, [number(r, key) for r in data.series[condition]],
                label=CONDITION_LABELS[condition], linewidth=1.6, markersize=3.2,
                **LINE_STYLES[condition])


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.png", dpi=230, bbox_inches="tight")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def make_figures(data):
    FIGURES.mkdir(parents=True, exist_ok=True)
    configure_plots()
    x = np.arange(len(data.names))
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.8), sharex=True, constrained_layout=True)
    for ax, key, label, color in zip(axes, ("classes", "dependencies"),
                                    ("Canonical internal classes", "Directed internal dependencies"), (TEAL, NAVY)):
        y = [integer(r, key) for r in data.sizes]
        ax.plot(x, y, color=color, marker="o", linewidth=1.8, markersize=3)
        ax.fill_between(x, y, color=color, alpha=.08)
        ax.set_ylabel(label)
        ax.set_ylim(bottom=0)
        ax.annotate(count(y[0]), (x[0], y[0]), xytext=(4, 7), textcoords="offset points", fontsize=8)
        ax.annotate(count(y[-1]), (x[-1], y[-1]), xytext=(-3, 7), textcoords="offset points", ha="right", fontsize=8)
    sample_ticks(axes[-1], data)
    save_figure(fig, "01_classes_dependencies")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 4.8), sharex=True, constrained_layout=True)
    axes[0].bar(x, [integer(r, "omnipresent_classes") for r in data.sizes], color=TEAL, width=.7)
    axes[0].set_ylabel("UE-removed classes")
    axes[1].plot(x, [100 * (1 - number(r, "edge_retention_fraction")) for r in data.sizes],
                 color=OCHRE, marker="o", markersize=3, linewidth=1.5)
    axes[1].set_ylabel("Dependencies removed (%)")
    axes[1].set_ylim(bottom=0)
    sample_ticks(axes[1], data)
    save_figure(fig, "02_ue_removals")

    fig, ax = plt.subplots(figsize=(7.6, 4.3), constrained_layout=True)
    condition_lines(ax, data, "mq")
    ax.axhline(0, color=MUTED, linewidth=.7)
    ax.set_ylabel("Lecture modularization quality (MQ)")
    sample_ticks(ax, data)
    ax.legend(loc="best", ncol=2, fontsize=8, frameon=True)
    save_figure(fig, "03_mq")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.8), sharex=True, constrained_layout=True)
    for ax, key in zip(axes, ("cohesion", "coupling")):
        condition_lines(ax, data, key)
        ax.set_ylabel("Macro " + key)
        ax.set_ylim(bottom=0)
    axes[0].legend(loc="best", ncol=2, fontsize=8, frameon=True)
    sample_ticks(axes[1], data)
    save_figure(fig, "04_cohesion_coupling")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.3), sharex=True, constrained_layout=True)
    for full, color, shift, label in [("A1", "#235C7E", -.19, "ACDC: A2 − projected A1"),
                                      ("A3", OCHRE, .19, "KMeans: A4 − projected A3")]:
        rows = data.comparison(full)
        axes[0].bar(x + shift, [number(r, "mq_change_same_graph") for r in rows], width=.36, color=color, label=label)
        axes[1].plot(x, [number(r, "adjusted_rand_agreement") for r in rows],
                     color=color, marker="o", markersize=3, linewidth=1.4, label=label.split(":")[0])
    axes[0].set_ylabel("MQ change on retained graph")
    axes[0].axhline(0, color=MUTED, linewidth=.7)
    axes[0].legend(fontsize=8, loc="best")
    axes[1].set_ylabel("Adjusted Rand agreement")
    axes[1].set_ylim(-.05, 1.05)
    sample_ticks(axes[1], data)
    save_figure(fig, "05_same_graph")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.2), sharex=True, constrained_layout=True)
    condition_lines(axes[0], data, "n_clusters")
    axes[0].set_ylabel("Recovered nonempty clusters")
    axes[0].legend(ncol=2, fontsize=8)
    for c in CONDITIONS:
        axes[1].plot(x, [100 * number(r, "max_cluster_size") / number(r, "n_nodes")
                         if number(r, "n_nodes") else 0 for r in data.series[c]],
                     label=c, linewidth=1.4, markersize=2.8, **LINE_STYLES[c])
    axes[1].set_ylabel("Largest cluster (% of nodes)")
    axes[1].set_ylim(bottom=0)
    sample_ticks(axes[1], data)
    save_figure(fig, "06_granularity")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.5), sharex=True, constrained_layout=True)
    tx = np.arange(1, len(data.names))
    axes[0].bar(tx, [integer(r, "added_classes") for r in data.evolution], color=TEAL, label="Added identities")
    axes[0].bar(tx, [-integer(r, "removed_classes") for r in data.evolution], color=OCHRE, label="Removed identities")
    axes[0].set_ylabel("Class identity changes")
    axes[0].axhline(0, color=MUTED, linewidth=.7)
    axes[0].legend(ncol=2, fontsize=8)
    for key, label, color, style in [("common_node_edge_jaccard", "Edge Jaccard", TEAL, "-"),
                                    ("acdc_adjusted_rand", "ACDC partition ARI", "#235C7E", "--"),
                                    ("kmeans_adjusted_rand", "KMeans partition ARI", OCHRE, "-.")]:
        axes[1].plot(tx, [number(r, key) for r in data.evolution], label=label, color=color,
                     linestyle=style, marker="o", markersize=3, linewidth=1.3)
    axes[1].set_ylabel("Agreement on common identities")
    axes[1].set_ylim(-.05, 1.05)
    axes[1].legend(ncol=3, fontsize=7.5)
    sample_ticks(axes[1], data)
    save_figure(fig, "07_temporal_change")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.7), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.1, 1]})
    stages = ["extraction", "UE", "A1", "A2", "A3", "A4"]
    stage_times = {s: [number(r, "seconds") for r in data.runtimes if r["stage"] == s] for s in stages}
    axes[0].barh(stages[::-1], [statistics.median(stage_times[s]) for s in stages[::-1]], color=TEAL)
    axes[0].set_xlabel("Median seconds per release")
    axes[0].set_title("Recorded study stages")
    cases = data.benchmark["cases"]
    axes[1].plot([c["distinct_member_references"] / 1000 for c in cases],
                 [c["median_seconds"] for c in cases], color=OCHRE, marker="o", linewidth=1.7)
    axes[1].set_xlabel("Distinct member references (thousands)")
    axes[1].set_ylabel("Median seconds, 3 repeats")
    axes[1].set_title("UE detector synthetic scaling")
    axes[1].set_ylim(bottom=0)
    save_figure(fig, "08_performance")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 4.9), sharex=True, constrained_layout=True)
    axes[0].plot(x, [r["annotations"] for r in data.class_breakdown], color=TEAL, marker="o", markersize=3)
    axes[0].set_ylabel("Owned annotation types")
    axes[0].set_ylim(bottom=0)
    axes[1].plot(x, [r["isolates"] for r in data.class_breakdown], color=NAVY, marker="o", markersize=3, label="All isolates")
    axes[1].plot(x, [r["annotation_isolates"] for r in data.class_breakdown], color=OCHRE, marker="s", markersize=3, linestyle="--", label="Annotation isolates")
    axes[1].set_ylabel("Primary-graph isolated types")
    axes[1].set_ylim(bottom=0)
    axes[1].legend(fontsize=8)
    sample_ticks(axes[1], data)
    save_figure(fig, "09_metadata_isolates")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.3), constrained_layout=True)
    curve = data.calibration["selection"]["curve"]
    chosen = data.calibration["pilot_k"]
    axes[0].plot([r["k"] for r in curve], [r["inertia"] for r in curve], color=TEAL, marker="o", markersize=3)
    axes[0].axvline(chosen, color=OCHRE, linestyle="--", label=f"Selected k={chosen}")
    axes[0].set_xlabel("Candidate k on pilot only")
    axes[0].set_ylabel("Within-cluster squared-distance inertia")
    axes[0].legend(fontsize=8)
    axes[1].plot([r["k"] for r in curve], [r["chord_gap"] for r in curve], color=NAVY, marker="o", markersize=3)
    axes[1].axvline(chosen, color=OCHRE, linestyle="--")
    axes[1].axhline(data.calibration["selection"]["minimum_gap"], color=MUTED, linewidth=.8, linestyle=":")
    axes[1].set_xlabel("Candidate k")
    axes[1].set_ylabel("Normalized gap below endpoint chord")
    save_figure(fig, "10_k_pilot")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.0), sharex=True, constrained_layout=True)
    for ax, full, label, color in zip(axes, ("A1", "A3"), ("ACDC", "KMeans"), (TEAL, OCHRE)):
        rows = data.comparison(full)
        ax.plot(x, [number(r, "mojofm_full_to_filtered") for r in rows], color=color, marker="o", markersize=3, label="Projected full → filtered")
        ax.plot(x, [number(r, "mojofm_filtered_to_full") for r in rows], color=color, marker="s", markersize=3, linestyle="--", label="Filtered → projected full")
        ax.set_ylabel(label + " MoJoFM (0–100)")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
    sample_ticks(axes[-1], data)
    save_figure(fig, "11_mojofm")


class ReportDoc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=57, bottomMargin=48, title="Guava: Software Evolution and Architecture Recovery",
                         author="EPL484 project study", subject="Thirty stable releases; ACDC, KMeans and Usage Equality",
                         creator="Reproducible ReportLab report generator", pageCompression=1)
        frame = Frame(MARGIN, 48, WIDTH, PAGE_H - 105, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0, id="normal")
        self.addPageTemplates(PageTemplate(id="normal", frames=[frame], onPage=self.decorate))
        self.bookmark_counter = 0

    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFont("Body", 7.2)
            canvas.setFillColor(colors.HexColor(MUTED))
            canvas.drawString(MARGIN, PAGE_H - 29, "GUAVA  /  SOFTWARE EVOLUTION & ARCHITECTURE RECOVERY")
            canvas.setStrokeColor(colors.HexColor("#D6E1E3"))
            canvas.line(MARGIN, PAGE_H - 37, PAGE_W - MARGIN, PAGE_H - 37)
        canvas.setFont("Body", 7.2)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(MARGIN, 27, "EPL484  ·  Reproducible project report  ·  30 stable releases")
        canvas.drawRightString(PAGE_W - MARGIN, 27, f"{doc.page:02d}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "Section":
            key = f"section-{self.bookmark_counter}"
            self.bookmark_counter += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, 0, False)


class ReportBuilder:
    def __init__(self, data):
        self.d = data
        self.styles = {
            "body": ParagraphStyle("BodyText", fontName="Body", fontSize=9.6, leading=14,
                                   textColor=colors.HexColor(NAVY), spaceAfter=8, allowWidows=0, allowOrphans=0),
            "small": ParagraphStyle("Small", fontName="Body", fontSize=8.2, leading=11.6,
                                    textColor=colors.HexColor(MUTED), spaceAfter=7),
            "tiny": ParagraphStyle("Tiny", fontName="Body", fontSize=7.1, leading=9.2,
                                   textColor=colors.HexColor(MUTED), spaceAfter=5),
            "section": ParagraphStyle("Section", fontName="Title-Bold", fontSize=21, leading=26,
                                      textColor=colors.HexColor(NAVY), spaceAfter=15, keepWithNext=1),
            "sub": ParagraphStyle("Subhead", fontName="Body-Bold", fontSize=11.3, leading=15,
                                  textColor=colors.HexColor(TEAL), spaceBefore=6, spaceAfter=7, keepWithNext=1),
            "caption": ParagraphStyle("Caption", fontName="Body", fontSize=8, leading=11,
                                      textColor=colors.HexColor(MUTED), spaceAfter=11),
            "cell": ParagraphStyle("Cell", fontName="Body", fontSize=7.7, leading=10.1,
                                   textColor=colors.HexColor(NAVY)),
            "cell_small": ParagraphStyle("CellSmall", fontName="Body", fontSize=6.9, leading=8.5,
                                         textColor=colors.HexColor(NAVY)),
            "header": ParagraphStyle("Header", fontName="Body-Bold", fontSize=7.5, leading=10,
                                     textColor=colors.white),
            "mono": ParagraphStyle("Mono", fontName="Mono", fontSize=7.8, leading=11.4,
                                   textColor=colors.HexColor(NAVY), spaceAfter=8, splitLongWords=1),
            "cover": ParagraphStyle("Cover", fontName="Title-Bold", fontSize=31, leading=39,
                                    textColor=colors.HexColor(NAVY), spaceAfter=19),
            "eyebrow": ParagraphStyle("Eyebrow", fontName="Body-Bold", fontSize=9, leading=14,
                                      textColor=colors.HexColor(TEAL), spaceAfter=17),
        }
        self.story = []
        self.sections = []

    def paragraph(self, text, style="body"):
        self.story.append(Paragraph(text, self.styles[style]))

    def heading(self, title):
        if self.story:
            self.story.append(PageBreak())
        if not title.startswith(("Appendix", "References")):
            title = f"{len(self.sections) + 1}  " + re.sub(r"^\d+\s+", "", title)
        self.sections.append(title)
        self.paragraph(title, "section")

    def sub(self, title):
        self.paragraph(title, "sub")

    def table(self, headers, rows, widths=None, small=False, numeric=(), padding=5):
        style = self.styles["cell_small" if small else "cell"]
        values = [[Paragraph(esc(v), self.styles["header"]) for v in headers]]
        values.extend([[Paragraph(str(v), style) for v in row] for row in rows])
        table = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
        commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), padding),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
            ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor(TEAL)),
        ]
        for row in range(1, len(values)):
            if row % 2 == 0:
                commands.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor(PALE)))
        # Paragraph alignment must also be set for genuinely right-aligned text.
        for column in numeric:
            for row in range(1, len(values)):
                values[row][column].style = ParagraphStyle("NumericCell", parent=style, alignment=TA_RIGHT)
        table.setStyle(TableStyle(commands))
        self.story.append(table)
        self.story.append(Spacer(1, 9))

    def chart(self, name, height=None, caption=""):
        image = Image(str(FIGURES / f"{name}.png"))
        ratio = image.imageHeight / image.imageWidth
        image.drawWidth = WIDTH
        image.drawHeight = WIDTH * ratio if height is None else height
        self.story.append(image)
        if caption:
            self.paragraph(caption, "caption")

    def formula(self, text):
        cell = Paragraph(text, ParagraphStyle("Formula", parent=self.styles["body"],
                                              fontSize=11, leading=17, spaceAfter=0))
        table = Table([[cell]], colWidths=[WIDTH])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PALE)),
                                   ("BOX", (0, 0), (-1, -1), .4, colors.HexColor("#CCDADB")),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 12),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                                   ("TOPPADDING", (0, 0), (-1, -1), 10),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        self.story.extend([table, Spacer(1, 11)])

    def cover(self):
        d = self.d
        self.story.append(Spacer(1, 37))
        self.paragraph("EPL484  /  SOFTWARE EVOLUTION  /  PROJECT 1", "eyebrow")
        self.paragraph("Guava<br/>Software evolution<br/>and architecture recovery", "cover")
        self.paragraph("A reproducible study of thirty sporadically selected stable Java releases, "
                       "revised with the instructor extractor, one release per major/minor family, a pilot-calibrated k rule, "
                       "and the supplied paper’s Usage Equality method.")
        self.story.append(Spacer(1, 17))
        self.table(["HISTORY", "EXPERIMENT", "BOUNDARY"], [
            ["<b>30 stable releases</b><br/>10.0 → 33.7.2", "<b>120 final partitions</b><br/>ACDC and KMeans × full/filtered", "<b>Internal classes only</b><br/>Merged inner/anonymous types"],
            ["30 distinct major/minor families", "Lecture MQ and MoJoFM agreement", "Instructor extractor; project-owned code"],
        ], [WIDTH / 3] * 3, padding=9)
        self.story.append(Spacer(1, 20))
        self.sub("Study boundary and evidence")
        self.paragraph(f"The observed graph grows from <b>{count(integer(d.first, 'classes'))}</b> to "
                       f"<b>{count(integer(d.last, 'classes'))} canonical classes</b>, and from "
                       f"<b>{count(integer(d.first, 'dependencies'))}</b> to <b>{count(integer(d.last, 'dependencies'))} "
                       "directed internal dependencies</b>. These are measurements of a static implementation view. "
                       "They are not a claim about Guava's intended architecture or its users' experience.")
        self.paragraph(f"Release window: {d.versions[0]['release_date'][:10]}–{d.versions[-1]['release_date'][:10]}. "
                       f"Dataset snapshot: {d.manifest['selection_date_utc'][:10]}. Repository: "
                       '<link href="https://github.com/google/guava" color="#247D72">github.com/google/guava</link>.', "small")
        self.paragraph("All measurements in this document are loaded from saved result files. Source code, "
                       "raw inputs, exact assignments and a machine-readable audit trail accompany the report. "
                       "Student names and contributions must be supplied truthfully by the submitting team.", "small")

    def revision(self):
        d = self.d
        self.heading("Revision record and controlled interpretation")
        self.paragraph("This report supersedes the original study published at commit d970305. The original "
                       "configuration, measurements and full repository history remain identifiable; compact tables "
                       "are preserved under results/baseline_v1. Revised observations are recomputed from the original "
                       "release artifacts under the following declared changes. [D17]")
        self.table(["Concern", "Revised decision"], [
            ["Custom annotation-heavy class graph", "Use the unmodified instructor extractor as the sole primary edge source. Keep custom member extraction separate for UE."],
            ["Public-suffix ownership", "Include Guava-owned com.google.thirdparty.publicsuffix implementation, alongside com.google.common."],
            ["Repeated patch families", "Select 30 distinct major/minor families from 45; one stable representative per family."],
            ["Weak square-root k heuristic", "Choose one middle-release inertia elbow, then freeze a size-calibrated k rule for the final series."],
            ["Lecture evaluation alignment", "Add directional MoJoFM agreement; retain supplemental ARI and the lecture-supported loop-free MQ formula."],
            ["UE versus older SIG detector", "Retain pure UE from the supplied paper; adding SIG would be a separately justified hybrid."],
        ], [153, WIDTH - 153], small=True)
        old_size = next(r for r in d.baseline_sizes if r["version"] == d.latest)
        self.table(["Latest release measurement", "Original study", "Revised study"], [
            ["Canonical classes", count(integer(old_size, "classes")), count(integer(d.last, "classes"))],
            ["Primary directed edges", count(integer(old_size, "dependencies")), count(integer(d.last, "dependencies"))],
            ["UE removals", count(integer(old_size, "omnipresent_classes")), count(integer(d.last, "omnipresent_classes"))],
            ["ACDC/full clusters", count(integer(next(r for r in d.baseline_metrics if r["version"] == d.latest and r["condition"] == "A1"), "n_clusters")), count(integer(d.by_metric[d.latest, "A1"], "n_clusters"))],
            ["KMeans/full clusters", count(integer(next(r for r in d.baseline_metrics if r["version"] == d.latest and r["condition"] == "A3"), "n_clusters")), count(integer(d.by_metric[d.latest, "A3"], "n_clusters"))],
        ], [WIDTH - 175, 85, 90], small=True, numeric=(1, 2), padding=3.5)
        comparison = d.graph_provenance[d.latest]
        self.paragraph(f"At the same revised ownership scope, the instructor graph has "
                       f"{count(comparison['dependencies'])} edges and the supplemental broad graph has "
                       f"{count(comparison['supplemental_dependencies'])}. They share {count(comparison['shared_edges'])}; "
                       f"{count(comparison['supplemental_only_edges'])} are supplemental-only, including "
                       f"{count(comparison['supplemental_only_annotation_target_edges'])} targeting annotation types. "
                       "The class CSV and comparison files preserve both models without mixing their edges. [D6]", "small")
        self.paragraph("The whole-study revision changes sampling, scope, graph policy and k together. A difference "
                       "between its aggregate scores and the original run cannot be attributed to a single change. "
                       "The same-version extractor comparison above controls the class scope; it is distinct from "
                       "the longitudinal before/after narrative. Better alignment and reproducibility do not prove "
                       "that a recovered partition is the intended architecture. [D17]", "small")

    def executive(self):
        d = self.d
        self.heading("1  Findings and experiment map")
        c_change = integer(d.last, "classes") / integer(d.first, "classes") - 1
        e_change = integer(d.last, "dependencies") / integer(d.first, "dependencies") - 1
        self.paragraph(f"<b>Structural scale increases across the sampled history.</b> Canonical classes change by "
                       f"{percent(c_change)} and internal directed dependencies by {percent(e_change)} between the endpoints. "
                       "Irregular sampling describes broad changes; it does not identify the exact intervening commit that caused them. "
                       "[D1; L12 pp.35–48]")
        removed = [integer(r, "omnipresent_classes") for r in d.sizes]
        self.paragraph(f"<b>Usage Equality produces an explicit, inspectable exclusion set.</b> The replacement detects "
                       f"{min(removed)}–{max(removed)} omnipresent classes per release; {len(d.removal_frequency)} distinct "
                       "class identities are detected at least once. Filtering removes those nodes and their incident edges from "
                       "the analysis graph. It does not delete code from Guava. [D1; D2]")
        for full, name in (("A1", "ACDC"), ("A3", "KMeans")):
            changes = [number(r, "mq_change_same_graph") for r in d.comparison(full)]
            n_positive = sum(v > 1e-12 for v in changes)
            n_negative = sum(v < -1e-12 for v in changes)
            self.paragraph(f"<b>{name}, after holding the evaluated graph fixed:</b> reclustering the retained graph "
                           f"increases MQ in {n_positive} sampled releases, decreases it in {n_negative}, and leaves it "
                           f"unchanged within 10<super>−12</super> in {30 - n_positive - n_negative}. This is a structural "
                           "metric result, without an authoritative architecture against which to measure accuracy. [D3]")
        self.table(["Condition", "Algorithm", "Graph evaluated"], [
            ["A1", "Original ACDC (+so, -l20)", "All canonical internal classes"],
            ["A2", "Same ACDC configuration", "Induced graph after UE removal"],
            ["A3", "Sparse normalized KMeans", "All canonical internal classes"],
            ["A4", "Same features and version-derived k", "Induced graph after UE removal"],
        ], [55, 194, WIDTH - 249])
        self.paragraph("The assignment requires all four conditions. The additional note requesting one analysis per version "
                       "is implemented as <b>one final partition per condition per release</b>, following a single-version pilot. "
                       "KMeans' ten internal initializations produce one fitted result. The latest-release AI experiment is "
                       "reported separately, as required by the assignment. [AS pp.2–4]")
        if (d.ai_dir / "metrics.json").exists():
            ai = read_json(d.ai_dir / "metrics.json")
            self.paragraph(f"<b>The recorded AI proposal groups the latest {ai['n_nodes']} classes into "
                           f"{ai['n_clusters']} named modules.</b> Its full-graph MQ is {fmt(ai['mq'], 4)} versus "
                           f"{fmt(d.metric('A3', 'mq'), 4)} for KMeans and {fmt(d.metric('A1', 'mq'), 4)} for ACDC. "
                           "The AI also sees names and package documentation, so this is not a controlled test of "
                           "superiority from identical information. Its conceptual boundaries and confidence limits "
                           "are discussed alongside the numerical result. [D12]")

    def selection(self):
        d = self.d
        self.heading("2  Subject and sporadic sampling")
        repo = d.eligibility["repository_metadata"]
        latest_inventory = read_json(ROOT / "data/provenance" / f"source_inventory_{d.latest}.json")
        self.paragraph("The students selected <b>google/guava</b>. The study follows the published main Guava JRE "
                       "artifact, providing a consistent production boundary across a long release history. This is a "
                       "library's implemented class architecture; other repository modules are outside the sampled artifact. [G1; D4]")
        self.table(["Course eligibility criterion", "Recorded evidence"], [
            ["Java; latest release ≥10,000 LOC", f"GitHub primary language: {esc(repo['language'])}. "
             f"{count(latest_inventory['source_owned_java_nonblank_noncomment_lines'])} nonblank, noncomment lines in owned Java sources."],
            ["GitHub repository created before 2024", esc(repo['created_at'][:10])],
            ["Not a fork; not archived", f"fork={str(repo['fork']).lower()}; archived={str(repo['archived']).lower()} at the recorded snapshot."],
            ["≥50 commits since 2024-01-01", "100 distinct qualifying commits retained as a lower-bound witness, rather than an inferred total."],
            ["≥10 major/minor releases", "30 stable releases covering exactly 30 distinct major/minor families."],
        ], [185, WIDTH - 185])
        self.paragraph(f"The eligibility SLOC count includes source-owned package descriptors. The narrower source-file "
                       f"population linked to canonical class nodes contains {count(integer(d.last, 'java_code_lines'))} "
                       "code lines at the latest release. Both exceed the requirement; the denominators are declared "
                       "rather than treated as interchangeable. [D4; D6]", "small")
        self.sub("Selection is specified before metric inspection")
        self.paragraph("The captured tag catalog contains 124 refs, of which 82 match the numeric stable-release "
                       "pattern. Forty-two nonmatching refs include prereleases, auxiliary artifacts and alternate tag "
                       "names; they are not all beta releases. Nine numeric releases before 10.0 are outside the defined "
                       "sampling window. The ambiguous 13.0 duplicate naming and two later backports to earlier lines "
                       "are also excluded, leaving 70 chronological mainline candidates. [D4]")
        self.formula("Family rank for sample i: <b>round(i × 44 / 29)</b>, &nbsp; i = 0,…,29")
        self.paragraph("The 70 eligible releases form 45 major/minor families. The rule selects 30 distinct families, "
                       "with one stable representative each. Use the highest eligible patch within a selected family, "
                       "except that the earliest family anchors the study at 10.0; the newest ends at 33.7.2. This "
                       "eliminates repeated observations from heavily patched families. [D4]")
        self.paragraph("Spacing is uniform in family rank, not calendar time. Some selected families are adjacent; "
                       "30 observations cannot all skip a family when only 45 families exist. A patch representative "
                       "is permitted, but a family appears only once. No release is removed because its graph is "
                       "identical or its MQ is inconvenient. Plain artifacts precede 23.1 and JRE artifacts follow "
                       "the variant split; Android is not a separate historical observation. [D4]", "small")
        self.paragraph("Eligibility evidence does not establish instructor approval. No teacher approval is represented "
                       "as observed. The publication dates of old releases come from Guava's release-history pages; "
                       "later dates use GitHub Release publication timestamps. Git commit dates remain separate fields. "
                       "[AS p.1; G2; D4]", "small")

    def provenance(self):
        d = self.d
        self.heading("3  Data acquisition and provenance")
        self.paragraph("Each selected release has an immutable Git commit identity and three Maven Central artifacts: "
                       "the production binary JAR, its source JAR and the POM. Acquisition reads public data and never "
                       "executes upstream Guava code. Published binaries avoid historical build failures becoming a "
                       "hidden release-selection criterion. [D4; D5]")
        self.table(["Evidence layer", "Stored and checked"], [
            ["Release identity", "Git tag name, 40-character commit SHA, published date, date basis and artifact coordinate."],
            ["Artifact integrity", "Pinned SHA-256 for every downloaded file; Maven SHA-1 sidecars; ZIP CRC checks; POM version/artifact identity."],
            ["Source ownership", "Per-source-file path and checksum, source-owned class inventory, SLOC definition and excluded binary entries."],
            ["Source-to-Git audit", "Every Java source-JAR file at the oldest and newest selected endpoints compared byte for byte with the pinned Git archive."],
            ["Offline reproducibility", "Cached artifacts must match existing pins; corrupt inputs are not silently overwritten."],
        ], [120, WIDTH - 120])
        endpoints = []
        for version in (d.names[0], d.names[-1]):
            check = read_json(ROOT / "data/provenance" / f"git_source_match_{version}.json")
            endpoints.append([version, count(check["compared_java_files"]), "All byte-identical" if check["all_sources_match"] else "Mismatch", check["commit_sha"][:12]])
        self.table(["Endpoint", "Java files", "Git/source result", "Commit prefix"], endpoints,
                   [60, 65, 220, WIDTH - 345], numeric=(1,))
        self.paragraph(f"All <b>{d.acquisition['artifact_count']} artifacts</b> ({d.acquisition['total_artifact_bytes'] / 1024**2:.2f} MiB) "
                       "passed pinned checks. Full Git-source correspondence was checked at the two endpoints; the "
                       "intermediate 28 releases have artifact and Git identity pins but are not claimed to have the same "
                       "complete per-file Git comparison. SHA sidecars fetched from the same repository provide integrity "
                       "evidence, not independent authorship authentication. PGP signatures were not verified. [D5]")
        self.sub("How to explain the data in the oral exam")
        self.paragraph("Start at a row in <font name='Mono'>config/versions.json</font>. Show its tag SHA and Maven URL, "
                       "hash the cached JAR, then inspect the source manifest and extractor provenance. Finally show how "
                       "the canonical class and edge CSVs become the algorithm inputs. This chain makes an individual "
                       "measurement traceable back to a concrete upstream artifact. [L4 pp.11–15]")
        self.paragraph("Audit pointers: config/versions.json; data/provenance/SHA256SUMS; acquisition.json; "
                       "source_inventory_&lt;version&gt;.json; git_source_match_10.0.json; git_source_match_33.7.2.json. "
                       "All paths are repository-relative.", "small")

    def structural_model(self):
        d = self.d
        self.heading("4  Instructor graph and ownership model")
        self.paragraph("<b>The unmodified instructor DependencyExtractor is the sole source of primary class edges.</b> "
                       "A supplemental ASM pass supplies a complete owned-class inventory, enclosing aliases and "
                       "resolved field/method evidence for UE. It does not augment the instructor graph with its "
                       "broader annotation, type or declaring-owner relationships. [TUT p.6; D6]")
        self.paragraph("The instructor receives a deterministic JAR containing owned base class entries copied "
                       "byte for byte from the original Maven binary. Per-entry hashes establish that no retained "
                       "class body was rewritten. The original full artifact remains preserved. An explicit classpath "
                       "launches the original CompCalc.MainClass with its unchanged bundled libraries. [D6]")
        self.table(["Evidence", "Role"], [
            ["classes.csv; class_aliases.csv", "Source-owned common/publicsuffix types; all genuine nested/local/anonymous identities merged by enclosing metadata."],
            ["instructor_raw.csv", "Original seven-category output, including occurrence counts retained for auditing."],
            ["dependencies_typed.csv; dependencies.csv", "Normalized instructor relationships; one typed pair, then one directed pair; no self-loops or external endpoints."],
            ["member_dependencies.csv", "Separate resolved method/field evidence for UE; original binary member identities remain distinct after class merging."],
            ["supplemental_dependencies.csv", "Explicitly separate broad graph for sensitivity auditing; never added to the primary graph."],
        ], [183, WIDTH - 183], small=True)
        self.paragraph("All seven tutorial relations are selected: EXTENDS, IMPLEMENTS, METHOD_CALL, METHOD_PARAMETER, "
                       "FIELD_REFERENCE, TYPE_USAGE and EXCEPTION_THROWS. The primary graph accepts the constructs "
                       "actually recognized by the supplied executable; it does not claim complete Java or runtime "
                       "coverage. Repeated occurrences and category overlap do not multiply edge weights. [TUT p.6]")
        self.table(["Class processing", d.names[0], d.latest], [
            ["Owned binary classes before merging", count(integer(d.first, "raw_binary_classes")), count(integer(d.last, "raw_binary_classes"))],
            ["Nested/anonymous identities merged", count(integer(d.first, "merged_binary_classes")), count(integer(d.last, "merged_binary_classes"))],
            ["Canonical project-owned types", count(integer(d.first, "classes")), count(integer(d.last, "classes"))],
            ["Owned annotation types", count(d.class_breakdown[0]["annotations"]), count(d.class_breakdown[-1]["annotations"])],
            ["Primary-graph isolates", count(d.class_breakdown[0]["isolates"]), count(d.class_breakdown[-1]["isolates"])],
        ], [WIDTH - 150, 75, 75], small=True, numeric=(1, 2), padding=3.3)
        self.paragraph("Both com.google.common and Guava-owned com.google.thirdparty.publicsuffix sources are included. "
                       "The public-suffix package carries Guava Authors headers; namespace naming alone was an "
                       "insufficient exclusion rule in the original study. JDK, failureaccess and external libraries "
                       "remain excluded at both edge endpoints. [D4; D6]", "small")
        self.paragraph("Owned annotation types remain nodes, including isolates. Supplemental annotation-application "
                       "edges are not added. A Guava API marked @Beta is still part of a stable release. Module/package "
                       "descriptors and multi-release overrides are excluded. Static analysis omits arbitrary reflection, "
                       "erased constants and full virtual-dispatch expansion. [D6]", "small")

    def ue_method(self):
        self.heading("5  Replacement JNode: Usage Equality")
        self.paragraph("<b>JNode-UE implements Yano and Matsuo's Usage Equality method.</b> It is the replacement "
                       "requested for this assignment, grounded in the supplied 2020 paper. It is not a reproduction "
                       "of the older JNode/Noise method based on ComponentRank and shortest-path significance. "
                       "This methodological substitution is explicit. [UE pp.663–664; L67 pp.46–47; D2]")
        self.formula("D<sub>M</sub>(A,B) = Σ<sub>m ∈ M(A,B)</sub> 1 / [xm_fanin(m) × mx(B)]<br/>"
                     "e(B) = 1 − max<sub>A</sub> D<sub>M</sub>(A,B)<br/>"
                     "c(B) = 1 − 1 / fanin(B)<br/>"
                     "Remove B exactly when <b>e(B) ≥ 0.85</b> and <b>c(B) ≥ 0.90</b>.")
        self.table(["Term", "Precise meaning after class-owner normalization"], [
            ["M(A,B)", "Distinct members of B referenced by members belonging to caller class A."],
            ["xm_fanin(m)", "Distinct source members outside B that reference target member m; not caller classes."],
            ["mx(B)", "Number of B's distinct members referenced from outside B; unreferenced members do not enter the denominator."],
            ["fanin(B)", "Number of distinct other internal project classes with resolved member use of B."],
        ], [90, WIDTH - 90])
        self.paragraph("The cardinality threshold requires at least ten caller classes. A class without incoming "
                       "member use has undefined scores and is retained. Scores are computed on the original graph once; "
                       "all qualifying nodes are removed simultaneously. No repeated cascade or per-release threshold "
                       "search is performed. “Outside B” means another owned class, not an external library. "
                       "Every score, strongest caller and decision is saved. [UE; D2]")
        self.sub("A small example explains the difference from degree")
        self.paragraph("Suppose one utility operation is referenced by one member in each of ten caller classes. "
                       "Each caller's dedication is 1/10, so e = c = 0.90 and the utility qualifies. Now imagine a "
                       "logger shared by 21 callers, where a startup class alone also uses a separate initialization "
                       "operation. Startup's dedication is 1/(21×2) + 1/(1×2), making e approximately 0.476. "
                       "That exclusive relationship prevents removal despite high fan-in. This is a constructed "
                       "explanatory example, not a Guava measurement. [UE Fig.1; D2]")
        self.paragraph("Implementation: set/dictionary aggregation over distinct member references; cached declaring "
                       "owners; stable summation and exact rational fallback at threshold boundaries. Expected core "
                       "aggregation is O(R + C + N), plus deterministic output sorting, where R is unique member "
                       "references, C caller–target class pairs and N classes. No all-pairs shortest paths are required. [D2]", "small")

    def recovery_methods(self):
        d = self.d
        self.heading("6  Two recovery methods, frozen rules")
        self.sub("ACDC: the original implementation")
        self.paragraph("The archived York Java implementation is compiled and invoked using <font name='Mono'>+so -l20</font>. "
                       "SubGraph Dominator runs before Orphan Adoption. The BodyHeader pattern matches C source/header "
                       "pairs and provides no Java class-level evidence here. The default fine, flat DownInducer output "
                       "is preserved. [TUT pp.7–8; L67 pp.19–24; ACDC; D7]")
        self.paragraph("The maximum-size parameter governs SubGraph construction, <b>not every final cluster</b>. "
                       "ACDC can place remaining orphans into a large final container. This output is reported without "
                       "post-hoc splitting. Dependency-only RSF cannot encode isolates, so known genuine isolates are "
                       "restored as explicit singleton clusters. All other classes must appear exactly once in ACDC's "
                       "output. Invalid, duplicate, missing or stale output is rejected. [D7]")
        self.sub("KMeans: fixed structural coordinates")
        self.formula("U = sorted union of class identities across all 30 releases<br/>"
                     "X = row-L2-normalize([A + I, (A + I)<super>T</super>])<br/>"
                     "k<sub>full</sub> = max(1, ceil(n<sub>full</sub> × k<sub>pilot</sub> / n<sub>pilot</sub>))<br/>"
                     "k<sub>filtered</sub> = min(k<sub>full</sub>, n<sub>filtered</sub>)")
        self.paragraph(f"Each current class is a row in a sparse CSR matrix with <b>{count(d.run['feature_dimensions'])} "
                       f"fixed columns</b> (two directions × {count(d.run['feature_universe_size'])} union identities). "
                       "Absent or removed coordinates contain zero evidence. Identity entries encode self-similarity "
                       "only in features; they never enter the dependency graph or metric calculation. Package names "
                       "and AI cluster labels are not features. [D7]")
        self.paragraph(f"The single middle-release inertia pilot selects k={d.calibration['pilot_k']} for "
                       f"n={d.calibration['pilot_n']} classes, implying an approximate target of "
                       f"{d.calibration['target_mean_class_count']:.2f} classes per cluster. Scaling that value with "
                       "full-graph size is an explicit extrapolation assumption. It is not a lecture theorem, a "
                       "guaranteed optimum, or a choice made by maximizing final MQ. [D7; D8]")
        self.paragraph("A3/A4 share the full-release-derived k, subject to the retained-node limit. Empty graphs "
                       "use k=0. A reviewer can choose --k for a separate exploratory run; the 120 final partitions "
                       "continue to use one frozen policy. The matched-ACDC-k pilot diagnostic below examines "
                       "granularity without using its quality result to select k. [D8]", "small")
        self.paragraph("KMeans uses k-means++ initialization, Lloyd updates, random_state=484, n_init=10, max_iter=300 "
                       "and tol=10<super>−4</super>; numerical thread pools are limited to one. Class order and output "
                       "labels are canonical. Actual k, convergence warnings, iterations, inertia and library versions "
                       "are recorded, so identical rows producing fewer clusters cannot go unnoticed. [SK; D7]", "small")

    def pilot(self):
        d = self.d
        pilot, calibration = d.pilot, d.calibration
        self.heading("7  Pilot and final parameter decision")
        self.paragraph(f"The pilot uses <b>Guava {esc(pilot['version'])}</b>, the middle selected release by sample "
                       "index, chosen before inspecting its quality. ACDC uses subgraph sizes 10, 20 and 40. "
                       "KMeans uses one declared candidate grid on this release only; final versions are not tuned "
                       "independently. The pilot outputs are separate from the 120 final A1–A4 architectures. [D8]")
        rows = []
        for trial in pilot["trials"]:
            m = trial["metrics"]
            label = f"ACDC -l{trial['max_subgraph_size']}" if trial["algorithm"] == "ACDC" else "KMeans (pilot elbow)"
            rows.append([label, count(m["n_clusters"]), count(m["max_cluster_size"]), count(m["singleton_clusters"]),
                         fmt(m["cohesion"]), fmt(m["coupling"]), fmt(m["mq"])])
        diagnostic = pilot.get("matched_acdc_k_diagnostic")
        if diagnostic:
            m = diagnostic["metrics"]
            rows.append(["KMeans (matched k diagnostic)", count(m["n_clusters"]), count(m["max_cluster_size"]),
                         count(m["singleton_clusters"]), fmt(m["cohesion"]), fmt(m["coupling"]), fmt(m["mq"])])
        self.table(["Pilot configuration", "k", "Largest", "Singles", "Cohesion", "Coupling", "MQ"], rows,
                   [142, 35, 54, 46, 73, 73, WIDTH - 423], small=True, numeric=tuple(range(1, 7)))
        acdc_trials = [t for t in pilot["trials"] if t["algorithm"] == "ACDC"]
        same = len({tuple(t["metrics"][k] for k in ("n_clusters", "cohesion", "coupling", "mq")) for t in acdc_trials}) == 1
        self.paragraph("All three ACDC settings have identical required metrics on this pilot; retaining the documented "
                       "middle setting has no measured disadvantage here. This is not a theorem of parameter "
                       "insensitivity. [D8]" if same else
                       "The ACDC pilot table exposes the actual parameter sensitivity. The final configuration retains "
                       "the documented +so/-l20 rule globally; a larger single-pilot MQ does not establish a better "
                       "architecture across the history. [D8]")
        if diagnostic:
            selected = next(t["metrics"] for t in pilot["trials"] if t["algorithm"] != "ACDC")
            acdc = next(t["metrics"] for t in acdc_trials if t["max_subgraph_size"] == 20)
            self.paragraph(f"At matched pilot k={diagnostic['k']}, ACDC MQ is {fmt(acdc['mq'], 4)} and KMeans MQ is "
                           f"{fmt(diagnostic['metrics']['mq'], 4)}. The elbow-selected KMeans MQ is "
                           f"{fmt(selected['mq'], 4)}. This diagnostic controls cluster count on this graph, not "
                           "cluster-size distribution or semantic validity, and does not determine the final k. [D8]")
        self.sub("ACDC identifier compatibility")
        self.paragraph("The file-oriented upstream implementation strips a final dotted suffix to form a basename. "
                       "The adapter reversibly maps p.A to p.A.java so distinct Java names cannot collapse to the "
                       "same package basename. It preserves each edge, saves node_id_map.csv and decodes every "
                       "membership before evaluation. The original ACDC source is unchanged. Real isolates are "
                       "restored as singletons; -l20 is a SubGraph-stage limit, not a final global size cap. [D7]")
        self.formula("Frozen configuration SHA-256:<br/><font name='Mono' size='8'>" + esc(d.run["config_sha256"]) + "</font>")
        self.heading("The single-pilot inertia curve")
        self.chart("10_k_pilot", caption="Figure 10. The fixed candidate grid's inertia and normalized elbow gap. "
                   "The selected k uses inertia geometry, not MQ. Source: results/pilot/k_inertia_curve.csv.")
        selection = calibration["selection"]
        self.table(["Candidate k", "Inertia", "Normalized gap", "Decision"], [
            [str(r["k"]), fmt(r["inertia"], 4), fmt(r["chord_gap"], 4), "Selected" if r["k"] == calibration["pilot_k"] else ""]
            for r in selection["curve"]], [85, 133, 135, WIDTH - 353], small=True, numeric=(0, 1, 2), padding=3)
        self.paragraph(f"Normalize x=(k−k_min)/(k_max−k_min) and y=(I−I_last)/(I_first−I_last); gap=1−x−y. "
                       f"Choose the largest interior gap if it is at least {selection['minimum_gap']:.2f}; exact ties "
                       "choose smaller k. Otherwise use the declared nearest candidate to k=30. "
                       f"Observed decision: {esc(selection['reason'])}; selected k={calibration['pilot_k']}; "
                       f"maximum gap={selection['maximum_interior_gap']:.4f}. [D8]", "small")
        self.paragraph("An elbow depends on the candidate range, feature geometry and optimization fits. It estimates "
                       "diminishing distance-fit returns on one graph, not the number of true components. The "
                       "observed elbow is broad: neighboring k candidates have similar gaps. The subsequent size scaling "
                       "preserves a target average granularity without another per-release "
                       "sweep. This assumption is disclosed and actual output sizes are reported. [D8]", "small")

    def quality(self):
        self.heading("8  Exact lecture quality measures")
        self.paragraph("The report uses the modularization-quality definition shown in the reconstruction lecture: "
                       "mean cluster cohesion minus mean coupling over unordered cluster pairs. Edges are directed, "
                       "binary and without self-loops. Let n<sub>i</sub> be cluster size, μ<sub>i</sub> its internal "
                       "edge count and ε<sub>ij</sub> the inter-cluster edge count in both directions. [L67 pp.15–17]")
        self.formula("cohesion<sub>i</sub> = μ<sub>i</sub> / [n<sub>i</sub>(n<sub>i</sub> − 1)] for n<sub>i</sub> &gt; 1; otherwise 0<br/>"
                     "coupling<sub>ij</sub> = ε<sub>ij</sub> / (2n<sub>i</sub>n<sub>j</sub>)<br/>"
                     "MQ = (1/k) Σ<sub>i</sub> cohesion<sub>i</sub> − (1 / choose(k,2)) Σ<sub>i&lt;j</sub> coupling<sub>ij</sub>")
        self.paragraph("The lecture presents alternative internal-density denominators; this study follows the "
                       "n(n−1) form used in its worked directed-graph example. A singleton's cohesion is zero. For "
                       "k=1, coupling is zero. Empty partitions report zero by explicit convention. Every zero-edge "
                       "cluster pair remains in the coupling average. These policies are declared because otherwise "
                       "software implementations can compute different values from the same partition. [L67 p.17; D9]")
        self.sub("A hand-calculable oracle")
        self.paragraph("Take clusters C1={a,b} and C2={c,d}, with edges a→b, b→a, c→d, d→c and b→c. "
                       "Each cluster has cohesion 2/(2×1)=1. Pair coupling is 1/(2×2×2)=1/8. Therefore "
                       "<b>MQ=1−1/8=0.875</b>. Adding a separate isolated singleton gives mean cohesion 2/3 "
                       "and mean coupling (1/8)/3=1/24, hence MQ=5/8. The changed score comes from the declared "
                       "averaging rule, although the original five edges are unchanged. [D9]")
        self.sub("What the numbers do and do not establish")
        self.paragraph("MQ is bounded between −1 and 1 for this model. It measures structural concentration, not "
                       "functional correctness, runtime performance, developer productivity or user-perceived quality. "
                       "Macro averaging gives a tiny cluster the same weight as a large one; changing k, isolate "
                       "handling or cluster sizes can change the score. Node-size-weighted cohesion, edge fractions "
                       "and cluster-size distributions are therefore reported as diagnostics. [L67 p.16; L12 p.45; D9]")
        self.paragraph("A1 and A3 share the full graph; A2 and A4 share the retained graph. Direct full-versus-filtered "
                       "MQ differences change both the grouping and the population. The same-graph comparison later "
                       "projects the full partition onto exactly the retained nodes and edges before evaluating it. "
                       "MoJoFM and supplementary Adjusted Rand values compare partitions without treating either as ground truth. [D3; D9; D16]", "small")

    def growth(self):
        d = self.d
        self.heading("9  Classes and dependencies over time")
        self.chart("01_classes_dependencies", caption="Figure 1. Canonical project-owned types and binary directed "
                   "instructor dependencies for 30 distinct major/minor families. Source: results/sizes.csv.")
        self.paragraph(f"The first selected release contains {count(integer(d.first, 'classes'))} classes and "
                       f"{count(integer(d.first, 'dependencies'))} dependencies; the last contains "
                       f"{count(integer(d.last, 'classes'))} classes and {count(integer(d.last, 'dependencies'))} dependencies. "
                       "Class counts include owned annotation types and isolates. The primary edge series no longer "
                       "includes supplemental annotation-application edges. [D1; D6]")
        self.paragraph("The equal horizontal spacing represents ordered observations, not equal elapsed time. The "
                       "family-first sample deliberately reduces repeated patch observations but is not calendar-uniform. "
                       "Different compiler output and static-analysis coverage can affect observed relations. A count "
                       "increase alone does not establish feature growth or worsening design. [L12 pp.43–48; D4]", "small")
        transitions = sorted(d.evolution, key=lambda r: abs(integer(d.by_version[r["version"]], "dependencies") -
                             integer(d.by_version[r["previous_version"]], "dependencies")), reverse=True)[:2]
        for transition in transitions:
            before = d.by_version[transition["previous_version"]]
            after = d.by_version[transition["version"]]
            self.paragraph(f"Observed transition {esc(transition['previous_version'])} → {esc(transition['version'])}: "
                           f"{count(integer(before, 'dependencies'))} → {count(integer(after, 'dependencies'))} primary edges. "
                           "The change-point audit preserves the added/removed identities and edges for source inspection; "
                           "sparse sampling does not identify the single causing commit. [D15]", "small")

    def metadata_breakdown(self):
        d = self.d
        self.heading("Metadata types and graph isolates")
        self.chart("09_metadata_isolates", caption="Figure 9. Owned annotation-type counts and graph isolates under the "
                   "instructor baseline. Annotation types remain in the node inventory; annotation-application edges "
                   "from the supplemental reader are not added. Source: classes.csv and dependencies.csv for each release.")
        first, last = d.class_breakdown[0], d.class_breakdown[-1]
        self.table(["Inventory category", d.names[0], d.latest], [
            ["All canonical project-owned types", count(first["classes"]), count(last["classes"])],
            ["Nonannotation types", count(first["non_annotations"]), count(last["non_annotations"])],
            ["Annotation types", count(first["annotations"]), count(last["annotations"])],
            ["All primary-graph isolates", count(first["isolates"]), count(last["isolates"])],
            ["Annotation isolates", count(first["annotation_isolates"]), count(last["annotation_isolates"])],
        ], [WIDTH - 160, 80, 80], small=True, numeric=(1, 2), padding=4)
        self.paragraph("Keeping all owned nodes prevents an edge-only inventory from silently discarding types. "
                       "It also has a measurable consequence: ACDC restores isolates as singletons, whose cohesion "
                       "is zero under the declared metric convention. KMeans receives identity-based feature rows "
                       "for isolates. Metadata types can therefore still affect node, cluster and MQ counts even "
                       "though their annotation applications are absent from the primary edge graph. [D6; D9]")
        self.paragraph("These categories overlap: an annotation isolate is both an annotation type and an isolate; "
                       "the table rows must not be added together. An absence of observed member use does not make "
                       "a type a UE removal. The detector retains the no-evidence case explicitly. [D2]", "small")

    def release_table(self):
        d = self.d
        self.heading("10  Complete thirty-release inventory")
        rows = []
        for version, size in zip(d.versions, d.sizes):
            rows.append([version["version"], version["release_date"][:10], count(integer(size, "classes")),
                         count(integer(size, "dependencies")), count(integer(size, "omnipresent_classes")),
                         count(integer(size, "retained_dependencies")),
                         str(len(version["skipped_stable_since_previous"])) if version["index"] > 1 else "—"])
        self.table(["Release", "Published", "Classes", "Edges", "UE out", "Edges left", "Skipped"], rows,
                   [62, 77, 64, 74, 53, 80, WIDTH - 410], small=True, numeric=(2, 3, 4, 5, 6), padding=3.5)
        self.paragraph("Classes are canonical owned nodes; edges are distinct directed dependencies. “UE out” counts "
                       "removed nodes. “Skipped” counts numeric stable tags strictly between the current and previous "
                       "sampled release, including any explicitly excluded mainline/backport point in that interval. "
                       "Exact intervening names, Git SHAs and artifact variants are in config/versions.json. [D1; D4]", "small")

    def removals(self):
        d = self.d
        self.heading("11  What Usage Equality removes")
        self.chart("02_ue_removals", caption="Figure 2. Detected omnipresent nodes and the fraction of original graph edges "
                   "incident to removed nodes. Removal is simultaneous and uses fixed thresholds. Source: results/sizes.csv.")
        top = d.removal_frequency.most_common(4)
        if top:
            self.table(["Frequently removed class identity", "Releases detected / 30"],
                       [[esc(short_class(name)), str(n)] for name, n in top], [WIDTH - 126, 126], small=True, numeric=(1,), padding=3.5)
        self.paragraph(f"At the latest release, UE removes {integer(d.last, 'omnipresent_classes')} of "
                       f"{integer(d.last, 'classes')} classes and leaves {count(integer(d.last, 'retained_dependencies'))} "
                       f"dependencies ({percent(number(d.last, 'edge_retention_fraction'))} of the full graph). "
                       "A frequent removal is not proof that a class is badly designed. A utility may be useful and "
                       "correct while obscuring subsystem structure for a clustering algorithm. [UE; D1; D2]", "small")
        self.paragraph("Frequency counts use all 30 releases as the denominator, including releases in which an identity "
                       "does not yet exist. Full per-class scores distinguish absent classes, retained candidates and "
                       "detected classes. See results/versions/&lt;version&gt;/ue.json and omnipresent.csv.", "small")
        case_rows = []
        for case in d.ue_cases["cases"]:
            score = case["production_score"]
            case_rows.append([esc(short_class(case["class_name"])), str(score["fanin"]), str(score["referenced_members"]),
                              fmt(score["usage_equality"], 4), fmt(score["cardinality"], 4),
                              "Remove" if score["omnipresent"] else "Retain"])
        self.table(["Latest audited target", "Callers", "Members", "e", "c", "Decision"], case_rows,
                   [170, 57, 57, 66, 66, WIDTH - 416], small=True, numeric=(1, 2, 3, 4), padding=3.5)
        self.paragraph("Preconditions passes both thresholds. Iterators has many callers but a strong specialized "
                       "relationship with Iterables, giving a maximum dedication of about 0.502 and preventing "
                       "removal. The independent case audit preserves exact fractions, all caller scores and member-CSV "
                       "row evidence; names alone do not determine these decisions. [D14]", "small")

    def mq_results(self):
        d = self.d
        self.heading("12  Modularization quality results")
        self.chart("03_mq", caption="Figure 3. The four required MQ series. A1/A3 evaluate full graphs; A2/A4 evaluate "
                   "retained graphs. Cross-graph gaps are descriptive and must not be read as a causal filtering benefit.")
        rows = []
        for c in CONDITIONS:
            vals = [number(r, "mq") for r in d.series[c]]
            rows.append([CONDITION_LABELS[c], fmt(min(vals)), fmt(statistics.median(vals)), fmt(max(vals)), fmt(vals[-1])])
        self.table(["Condition", "Minimum", "Median", "Maximum", "Latest"], rows,
                   [185, 77, 77, 77, WIDTH - 416], numeric=(1, 2, 3, 4))
        full_wins = sum(d.metric("A1", "mq", v) > d.metric("A3", "mq", v) + 1e-12 for v in d.names)
        filtered_wins = sum(d.metric("A2", "mq", v) > d.metric("A4", "mq", v) + 1e-12 for v in d.names)
        self.paragraph(f"On the same full graph, ACDC has higher MQ than KMeans in {full_wins} of 30 releases; "
                       f"on the same filtered graph it has higher MQ in {filtered_wins}. This comparison describes "
                       "the chosen metric and granularity rules. It does not demonstrate that the higher-scoring "
                       "partition matches the intended subsystem architecture. Cluster counts and sizes are examined "
                       "alongside the score. [D1; D9]")

    def components(self):
        self.heading("13  Cohesion and coupling separately")
        self.chart("04_cohesion_coupling", caption="Figure 4. Required macro cohesion and macro coupling. Each panel has its "
                   "own vertical scale. Both quantities average over clusters or cluster pairs, not over classes.")
        self.paragraph("Showing the terms separately prevents a single MQ value from hiding its composition. A change "
                       "can come from denser internal groups, fewer cross-group edges, or a change in how cluster and "
                       "pair sizes are weighted. The coupling denominator also grows with the number of cluster pairs. "
                       "A low macro coupling score is therefore not equivalent to having few inter-cluster edges. [D9]")
        self.paragraph("For an oral explanation, choose any appendix row and open its corresponding "
                       "A&lt;n&gt;_quality/per_cluster.csv and per_pair.csv. Sum the saved normalized terms, divide by "
                       "the numbers of clusters and unordered pairs, and subtract. The report's rounded values are "
                       "display values; the CSV and JSON outputs preserve the computation precision.", "small")

    def same_graph_results(self):
        d = self.d
        self.heading("14  Does filtering change the grouping?")
        self.chart("05_same_graph", caption="Figure 5. Recovered filtered partition versus the full partition projected to "
                   "the identical retained graph. Positive MQ difference favors reclustering under the lecture metric. "
                   "ARI is agreement, not correctness. Source: results/same_graph_comparisons.csv.")
        rows = []
        for full, name in (("A1", "ACDC"), ("A3", "KMeans")):
            comp = d.comparison(full)
            vals = [number(r, "mq_change_same_graph") for r in comp]
            rows.append([name, fmt(statistics.median(vals), 4), fmt(vals[-1], 4),
                         fmt(number(comp[-1], "adjusted_rand_agreement")),
                         str(sum(v > 1e-12 for v in vals)), str(sum(v < -1e-12 for v in vals))])
        self.table(["Algorithm", "Median ΔMQ", "Latest ΔMQ", "Latest ARI", "Δ > 0", "Δ < 0"], rows,
                   [85, 95, 93, 83, 68, WIDTH - 424], small=True, numeric=(1, 2, 3, 4, 5))
        self.paragraph("Projection removes the same classes from the full partition without reclustering the survivors. "
                       "Empty projected clusters disappear. Both projected and newly recovered assignments are then "
                       "evaluated using the exact same retained edges. This controls the evaluated population, making "
                       "the difference attributable to the grouping produced under the declared recovery process. "
                       "It still does not supply an expert architecture or prove a general benefit of removal. [D3]", "small")

    def agreement_results(self):
        d = self.d
        self.heading("Lecture agreement: directional MoJoFM")
        self.chart("11_mojofm", caption="Figure 11. MoJoFM after projecting full and filtered architectures onto the "
                   "same retained class universe. Forward and reverse scores use different reference partitions. "
                   "Scores are agreement on a 0–100 scale, not recovery accuracy. [D16]")
        rows = [r for r in d.partition_comparisons if r["version"] == d.latest and r["scope"] != "temporal_full_common"]
        self.table(["Latest comparison", "Nodes", "Forward", "Reverse", "ARI"], [
            [esc(r["source_condition"] + " → " + r["reference_condition"]), count(integer(r, "n_nodes")),
             fmt(number(r, "mojofm"), 2), fmt(number(r, "reverse_mojofm"), 2), fmt(number(r, "adjusted_rand_agreement"), 4)]
            for r in rows], [150, 65, 93, 93, WIDTH - 401], small=True, numeric=(1, 2, 3, 4))
        self.formula("MoJoFM(P → Q) = 100 × [1 − MoJo(P,Q) / maxMoJo(Q)]")
        self.paragraph("MoJo counts minimal moves and cluster joins toward a specified reference. Its normalizer "
                       "depends on that reference, so reversing the inputs can change the result. The saved table "
                       "contains distances, denominators, source/reference cluster counts, both directions and a "
                       "hash of the exact object universe. Empty or one-object normalized boundaries are recorded "
                       "as undefined rather than silently inventing a fraction. [L67; D16]", "small")
        self.paragraph("An expert reference is necessary to interpret a score as architecture recovery accuracy. "
                       "It is not necessary to calculate agreement between two stated partitions. This corrects the "
                       "original overly restrictive rationale for omitting MoJoFM. ARI remains a supplementary "
                       "symmetric agreement measure; neither measure assesses module names or intended responsibilities. "
                       "Temporal and AI comparisons apply the same object-universe rule. [D16]", "small")

    def granularity(self):
        d = self.d
        self.heading("15  Granularity and metric sensitivity")
        self.chart("06_granularity", caption="Figure 6. Number of recovered clusters and share of nodes in the largest "
                   "cluster. ACDC's subgraph-size setting is not a final cluster-size cap.")
        rows = []
        for c in CONDITIONS:
            r = d.by_metric[d.latest, c]
            rows.append([c, count(integer(r, "n_clusters")), count(integer(r, "max_cluster_size")),
                         count(integer(r, "singleton_clusters")), fmt(number(r, "size_weighted_cohesion")),
                         percent(number(r, "inter_edge_fraction"))])
        self.table(["Latest", "k", "Largest", "Singletons", "Size-weighted cohesion", "Inter-edge share"], rows,
                   [51, 43, 65, 74, 142, WIDTH - 375], small=True, numeric=(1, 2, 3, 4, 5))
        self.paragraph("The supplementary cohesion weights each cluster by its node count, while the required MQ "
                       "weights each nonempty cluster equally. Inter-edge share counts all edges crossing the partition "
                       "boundary and divides by the total edge count. Neither diagnostic is substituted for the lecture "
                       "metric. Their purpose is to reveal large residual containers or numerous tiny clusters that "
                       "the macro averages can conceal. [D9]", "small")

    def temporal(self):
        d = self.d
        self.heading("16  Structural change between samples")
        self.chart("07_temporal_change", caption="Figure 7. Canonical identity changes and structural agreement between "
                   "adjacent selected samples. Agreement uses common class identities; dates remain irregular.")
        churn = max(d.evolution, key=lambda r: integer(r, "added_classes") + integer(r, "removed_classes"))
        self.paragraph(f"The largest sampled identity turnover is {esc(churn['previous_version'])} → {esc(churn['version'])}: "
                       f"{integer(churn, 'added_classes')} added and {integer(churn, 'removed_classes')} removed identities. "
                       "An identity change can mean introduction, deletion, renaming, package migration or an observable "
                       "compiler/model change. It is not automatically feature growth or loss. [D10]")
        self.paragraph("The public-suffix implementation remains inside the revised project boundary. Its historical "
                       "move from com.google.common.net to com.google.thirdparty.publicsuffix no longer excludes that "
                       "functionality by namespace, although a name-based comparison can still count a rename as one "
                       "removed and one added identity. [D4; D6]", "small")
        self.paragraph("Common-node edge Jaccard evaluates only dependencies among surviving identities. It can remain "
                       "high while total edge counts change through newly added or removed classes. Temporal MoJoFM "
                       "and ARI compare the projected A1/A3 partitions on those same common identities. They are "
                       "partition stability measures, not evidence of intended-architecture accuracy. [D10; D16]", "small")

    def change_evidence(self):
        d = self.d
        self.heading("Source evidence for observed transitions")
        points = {(p["before_version"], p["after_version"]): p for p in d.changes["change_points"]}
        selected = [("13.0.1", "15.0"), ("19.0", "21.0"), ("33.2.1", "33.4.8"), ("33.4.8", "33.5.0")]
        self.table(["Sample transition", "Classes", "Edges", "Edge change"], [
            [esc(a + " → " + b), f"{points[a,b]['counts']['classes_before']} → {points[a,b]['counts']['classes_after']}",
             f"{points[a,b]['counts']['edges_before']} → {points[a,b]['counts']['edges_after']}",
             fmt(points[a,b]["counts"]["edge_change_percent"], 2) + "%"] for a, b in selected
        ], [143, 107, 130, WIDTH - 380], small=True, padding=4)
        point = points["13.0.1", "15.0"]
        self.sub("Collections, escaping and I/O between 13.0.1 and 15.0")
        self.paragraph(f"The audit observes {point['counts']['added_classes']} added and "
                       f"{point['counts']['removed_classes']} removed canonical identities. Added groups include "
                       f"{point['added_classes_by_package']['com.google.common.collect']} collection types, "
                       f"{point['added_classes_by_package']['com.google.common.escape']} escaping types and "
                       f"{point['added_classes_by_package']['com.google.common.io']} I/O types. Examples include "
                       "ImmutableRangeMap and ImmutableRangeSet. Source-JAR entry hashes and exact edge differences "
                       "support the inventory claim. They do not turn every implementation type into a new user feature. [D15]")
        point = points["19.0", "21.0"]
        self.sub("Graph package observed by the 21.0 sample")
        self.paragraph(f"Of {point['counts']['added_classes']} added identities, "
                       f"{point['added_classes_by_package']['com.google.common.graph']} are under com.google.common.graph. "
                       f"The common-node edge Jaccard remains {fmt(point['counts']['common_node_edge_jaccard'], 4)}, "
                       "so much of the increase accompanies added types while many surviving-node relationships "
                       "remain stable. The interval also contains an unsampled release; this does not locate the "
                       "first introduction commit. [D15]")
        point = points["33.2.1", "33.4.8"]
        self.sub("Nullness migration affects the inventory more than primary edges")
        self.paragraph(f"The source audit finds the earlier internal ElementTypesAreNonnullByDefault declaration "
                       "and its use in Lists.java, then the later package-level @NullMarked and JSpecify import. "
                       f"There are {point['counts']['removed_annotation_classes']} removed and "
                       f"{point['counts']['added_annotation_classes']} added annotation types, while primary edges "
                       f"change by only {fmt(point['counts']['edge_change_percent'], 2)}%. The annotation applications "
                       "are outside the primary instructor relation model, so the earlier metadata-driven edge "
                       "spike/fall is not imported into this series. Metadata nodes still affect node and isolate counts. [D15]")
        point = points["33.4.8", "33.5.0"]
        self.sub("Collection support changes at 33.5.0")
        self.paragraph(f"All {point['counts']['removed_classes']} removed identities are collection types; seven "
                       "are nonannotation types and one is GwtTransient. The list includes GWT serialization "
                       "dependency helpers, ForwardingImmutableCollection and ImmutableEntry. "
                       f"The audit records {point['counts']['removed_edges']} removed and "
                       f"{point['counts']['added_edges']} added edges. These are observed implementation changes, "
                       "not by themselves proof of architectural repair or public-feature loss. [D15]", "small")

    def cluster_profiles(self):
        d = self.d
        self.heading("17  Reading the latest recovered groups")
        self.paragraph("A partition is more explainable when its members are inspected. The tables below show the "
                       "five largest clusters from each full-graph recovery at the latest release. Package composition "
                       "is computed after clustering as a descriptive aid; package labels were not algorithm features. "
                       "Cluster identifiers are canonical output labels, not authoritative subsystem names. [D7]")
        for c in ("A1", "A3"):
            self.sub(CONDITION_LABELS[c])
            members = defaultdict(list)
            for row in d.latest_partition(c):
                members[row["cluster"]].append(row["class"])
            rows = []
            for cluster, names in sorted(members.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:5]:
                packages = Counter(n.rsplit(".", 1)[0].removeprefix("com.google.common.") for n in names)
                composition = "; ".join(f"{p}: {n}" for p, n in packages.most_common(3))
                examples = ", ".join(short_class(n) for n in sorted(names)[:3])
                rows.append([esc(cluster), str(len(names)), esc(composition) + "<br/><font color='#536470'>" + esc(examples) + "</font>"])
            self.table(["Cluster", "Nodes", "Dominant packages; example identities"], rows,
                       [76, 43, WIDTH - 119], small=True, numeric=(1,), padding=4.5)
        self.paragraph("For ACDC, the saved original_containers map links normalized labels to the implementation's "
                       "container names, including any orphan container. Inspect this map before assigning a semantic "
                       "meaning to a large group. Complete assignments remain available for every condition and release. "
                       "[D7]", "small")

    def ai_sections(self):
        """The AI experiment adapter is finalized once its actual saved schema exists."""
        d = self.d
        self.heading("18  Latest-release AI experiment")
        experiment = d.ai_dir / "experiment.json"
        if not experiment.exists():
            raise FileNotFoundError("The revised final report requires the actual new AI experiment record")
        record = read_json(experiment)
        d.inputs.append(experiment)
        self._ai_record(record)

    def _ai_record(self, record):
        """Render the actual live-model record; do not invent or rerun AI output."""
        d = self.d
        required = [record["assignment_file"], record["output_file"], record["architecture_file"],
                    "results/ai/initial_hypothesis.md", "results/ai/activity.json", "results/ai/metrics.json",
                    "results/ai/retained_metrics.json", "results/ai/comparisons.csv",
                    "results/ai/evaluation.json", "results/ai/partition_comparisons.json"]
        missing = [p for p in required if not (ROOT / p).exists()]
        if missing:
            raise FileNotFoundError("Wait for the genuine AI experiment and coordinator evaluation: " + ", ".join(missing))
        d.inputs.extend(ROOT / p for p in required)
        prompt_path = ROOT / record["prompt_file"]
        if sha256(prompt_path) != record["prompt_sha256"]:
            raise ValueError("Recorded AI prompt checksum differs from the supplied prompt")
        d.inputs.append(prompt_path)
        additional_prompts = sorted(record.get("additional_prompt_files", []), key=lambda item: item["sequence"])
        for item in additional_prompts:
            path = ROOT / item["path"]
            if sha256(path) != item["sha256"]:
                raise ValueError("Recorded additional AI prompt checksum mismatch: " + item["path"])
            d.inputs.append(path)
        for item in record["input_files"]:
            path = ROOT / item["path"]
            if sha256(path) != item["sha256"]:
                raise ValueError("Recorded AI input checksum mismatch: " + item["path"])
            d.inputs.append(path)
        architecture = read_json(ROOT / record["architecture_file"])
        assignment = read_csv(ROOT / record["assignment_file"])
        ai_classes = [r["class"] for r in assignment]
        expected_classes = {r["class"] for r in d.latest_partition("A1")}
        if len(ai_classes) != len(set(ai_classes)) or set(ai_classes) != expected_classes:
            raise ValueError("AI partition does not exactly cover the latest graph")
        module_counts = Counter(r["cluster"] for r in assignment)
        for module in architecture["modules"]:
            if module_counts[module["id"]] != module["class_count"]:
                raise ValueError("AI narrative module count differs from actual assignments")
        if {m["id"] for m in architecture["modules"]} != set(module_counts):
            raise ValueError("AI module inventory differs from actual assignment labels")
        metrics = read_json(d.ai_dir / "metrics.json")
        retained = read_json(d.ai_dir / "retained_metrics.json")
        comparisons = read_csv(d.ai_dir / "comparisons.csv")
        if (metrics["n_nodes"], metrics["n_edges"]) != (integer(d.last, "classes"), integer(d.last, "dependencies")):
            raise ValueError("AI full metrics use a different graph")
        if (retained["n_nodes"], retained["n_edges"]) != (integer(d.last, "retained_classes"), integer(d.last, "retained_dependencies")):
            raise ValueError("AI retained metrics use a different graph")
        if len(comparisons) != 4 or {r["condition"] for r in comparisons} != set(CONDITIONS):
            raise ValueError("Expected four same-graph AI/baseline comparisons")
        evaluation = read_json(d.ai_dir / "evaluation.json")
        if evaluation["status"] != "passed" or evaluation["classes_assigned_exactly_once"] != len(ai_classes):
            raise ValueError("The recorded revised AI evaluation has not passed")
        for filename, expected_hash in evaluation["output_sha256"].items():
            if sha256(d.ai_dir / filename) != expected_hash:
                raise ValueError("AI output changed after evaluation: " + filename)
        for row in comparisons:
            reference = metrics if row["condition"] in ("A1", "A3") else retained
            baseline = d.by_metric[d.latest, row["condition"]]
            if (integer(row, "n_nodes"), integer(row, "n_edges")) != (reference["n_nodes"], reference["n_edges"]):
                raise ValueError("AI comparison population mismatch")
            if not math.isclose(number(row, "ai_mq"), reference["mq"], abs_tol=1e-12):
                raise ValueError("AI comparison score mismatch")
            if not math.isclose(number(row, "baseline_mq"), number(baseline, "mq"), abs_tol=1e-12):
                raise ValueError("Baseline comparison score mismatch")
        self.paragraph(f"<b>Recorded model:</b> {esc(record['model'])}. The subject is the same pinned Guava "
                       f"{esc(record['version'])} release used by the classical experiments. A fresh delegated session "
                       "first wrote a qualitative hypothesis from class names and package counts, then read the other "
                       "evidence and produced one complete final partition. The initial hypothesis is not a second "
                       "finalized architecture. [AS pp.3–4; D12]")
        self.table(["Exact supplied input", "Bytes", "SHA-256 prefix"], [
            [esc(Path(item["path"]).name), count(item["bytes"]), item["sha256"][:16]] for item in record["input_files"]
        ], [235, 70, WIDTH - 305], small=True, numeric=(1,))
        self.paragraph(f"The provided graph contains {count(metrics['n_nodes'])} classes and {count(metrics['n_edges'])} "
                       "directed dependencies. Package documentation is taken from the corresponding source JAR. "
                       "The protocol withholds ACDC/KMeans partitions, UE decisions and metric outcomes, forbids "
                       "external browsing, and requires complete one-module-per-class coverage before the coordinator "
                       "calculates quality. Exact full hashes, paths, activity and outputs are preserved. [D12]")
        self.sub("Information provided and reproducibility limits")
        for note in record["notes"]:
            self.paragraph(esc(note))
        self.paragraph("The initial hypothesis and the final explanation are saved separately as initial_hypothesis.md "
                       "and response.md. The following pages reproduce the actual prompt, enumerate the returned "
                       "modules, and evaluate that fixed output. Replaying the coordinator's calculations is "
                       "deterministic; rerunning a live model need not reproduce the same proposal. [D12]", "small")
        if additional_prompts:
            self.sub("Additional user-visible messages, verbatim")
            self.paragraph("The primary task prompt is reproduced on the next page. The exact additional recorded "
                           "instruction is reproduced below. It supplies no baseline partition or quality result. "
                           "The revision has no additional saved completion/status follow-up. [D12]", "tiny")
            for item in additional_prompts:
                path = ROOT / item["path"]
                label = "Launch instruction" if path.name == "launch_message.txt" else "Coordinator follow-up"
                self.paragraph(f"<b>{label}:</b> " + esc(path.read_text().strip()), "tiny")
                self.paragraph(f"SHA-256: {item['sha256']}", "tiny")

        self.heading("19  Exact prompt supplied to the AI")
        self.paragraph("The text below is the saved experiment prompt, reproduced without editorial changes. "
                       "Hidden platform instructions and model internals are not claimed to be part of this record. [D12]", "small")
        for block in prompt_path.read_text(encoding="utf-8").strip().split("\n\n"):
            self.paragraph(esc(block).replace("\n", "<br/>"), "small")
        self.paragraph("Prompt SHA-256: " + esc(record["prompt_sha256"]), "mono")

        self.heading("20  The AI's proposed conceptual modules")
        self.paragraph(f"The finalized AI assignment contains <b>{len(module_counts)} modules covering all "
                       f"{count(len(ai_classes))} supplied classes exactly once</b>. Responsibilities below are "
                       "the model's interpretation of the supplied names, documentation and dependencies. They are "
                       "not maintainer-approved design constraints. The machine-readable architecture also records "
                       "each boundary rationale and its supporting observations. [D12]")
        self.table(["Module", "Classes", "Responsibility excerpt"], [
            [esc(m["name"]), count(m["class_count"]), esc(excerpt(m["responsibility"], 155))] for m in architecture["modules"]
        ], [150, 48, WIDTH - 198], small=True, numeric=(1,), padding=3.2)
        self.paragraph("Complete class-level output: results/ai/assignment.csv. Complete semantic response: "
                       "results/ai/response.md. Initial hypothesis: results/ai/initial_hypothesis.md. Machine-readable "
                       "module definitions, refinements and limitations: results/ai/architecture.json. [D12]", "small")

        self.heading("21  AI quality and comparison")
        rows = []
        for label, graph, value in [("AI final", "Full", metrics), ("A1", "Full", d.by_metric[d.latest, "A1"]),
                                    ("A3", "Full", d.by_metric[d.latest, "A3"]),
                                    ("AI projected", "Retained", retained),
                                    ("A2", "Retained", d.by_metric[d.latest, "A2"]),
                                    ("A4", "Retained", d.by_metric[d.latest, "A4"])]:
            rows.append([label, graph, str(integer(value, "n_clusters")), fmt(number(value, "cohesion"), 4),
                         fmt(number(value, "coupling"), 4), fmt(number(value, "mq"), 4),
                         percent(number(value, "inter_edge_fraction"))])
        self.table(["Partition", "Graph", "k", "Cohesion", "Coupling", "MQ", "Inter-edge %"], rows,
                   [84, 62, 29, 80, 80, 75, WIDTH - 410], small=True, numeric=(2, 3, 4, 5, 6))
        self.paragraph("The AI's full assignment is evaluated on the same graph as A1/A3. For A2/A4 comparisons, "
                       "the same AI assignment is projected onto retained nodes and evaluated on retained edges, "
                       "without asking the model for another architecture. Cross-scope scores are not compared as "
                       "though they measured the same graph. Information supplied to the methods also differs: the "
                       "AI sees names and documentation, while KMeans receives structural features. [D12]")
        self.table(["Baseline", "Graph", "AI → baseline MoJoFM", "Baseline → AI MoJoFM", "ARI"], [
            [r["condition"], esc(r["graph"]), fmt(number(r, "mojofm_ai_to_baseline"), 2),
             fmt(number(r, "mojofm_baseline_to_ai"), 2), fmt(number(r, "adjusted_rand_agreement"), 4)] for r in comparisons
        ], [58, 71, 137, 137, WIDTH - 403], small=True, numeric=(2, 3, 4), padding=3.5)
        self.sub("Three concrete refinements from the added evidence")
        changes = architecture.get("changes_from_initial_hypothesis", [])
        if isinstance(changes, str):
            changes = [changes]
        for change in changes[:3]:
            if isinstance(change, dict):
                change = " ".join(str(change[k]) for k in ("final_decision", "evidence_and_reason") if k in change)
            self.paragraph(esc(change), "small")
        self.sub("Interpretation and confidence")
        ai_vs_kmeans = next(r for r in comparisons if r["condition"] == "A3")
        self.paragraph(f"AI MQ is {fmt(metrics['mq'], 4)} on the full graph and {fmt(retained['mq'], 4)} after "
                       f"projection. The AI uses {metrics['n_clusters']} modules and A3 uses "
                       f"{integer(d.by_metric[d.latest, 'A3'], 'n_clusters')} clusters; their adjusted Rand agreement "
                       f"is {fmt(number(ai_vs_kmeans, 'adjusted_rand_agreement'), 4)}. Aggregate MQ does not specify "
                       "which classes are grouped together. Granularity and information differ: the AI sees names "
                       "and source documentation, while the structural algorithms follow their own graph objectives. "
                       "No acyclic build decomposition or intended-design accuracy is established. [D9; D12]")
        ai_vs_acdc = next(r for r in comparisons if r["condition"] == "A1")
        self.paragraph(f"Direction matters: AI → A1 MoJoFM is {fmt(number(ai_vs_acdc, 'mojofm_ai_to_baseline'), 2)} "
                       f"but A1 → AI is {fmt(number(ai_vs_acdc, 'mojofm_baseline_to_ai'), 2)}. Moves can be necessary "
                       "to subdivide coarse groups, whereas joins can merge fine groups; the target also determines "
                       "normalization. Reporting one favorable direction would hide this asymmetry. [D12; D16]", "small")
        self.paragraph("Partition agreement and coordinator evaluation details: results/ai/comparisons.csv; "
                       "metrics.json; retained_metrics.json. The live model's complete limitations and "
                       "cross-module observations remain in architecture.json and response.md. [D12]", "small")

    def performance(self):
        d = self.d
        self.heading("22  Performance and scaling evidence")
        self.chart("08_performance", caption="Figure 8. Actual study-stage timings and a separate controlled synthetic "
                   "UE benchmark. They measure different scopes and are not speedup ratios.")
        rows = []
        for stage in ("extraction", "UE", "A1", "A2", "A3", "A4"):
            values = [number(r, "seconds") for r in d.runtimes if r["stage"] == stage]
            rows.append([stage, fmt(statistics.median(values), 4), fmt(max(values), 4), fmt(sum(values), 3)])
        self.table(["Study stage", "Median / release (s)", "Maximum (s)", "30-release sum (s)"], rows,
                   [92, 151, 104, WIDTH - 347], small=True, numeric=(1, 2, 3), padding=3.8)
        rows = [[count(c["classes"]), count(c["distinct_member_references"]), fmt(c["median_seconds"], 4),
                 fmt(c["process_high_water_rss_mib"], 1)] for c in d.benchmark["cases"]]
        self.table(["Synthetic N", "Member references", "Median (s)", "Process high-water MiB"], rows,
                   [92, 137, 97, WIDTH - 326], small=True, numeric=(0, 1, 2, 3), padding=3.8)
        self.paragraph("Study extraction includes JVM startup and I/O; UE study time includes member-CSV parsing; "
                       "clustering is wall time around each adapter. Downloads, the pilot, report generation and tests "
                       "are not included in the stage sums. Synthetic timings isolate the detector including validation "
                       "and diagnostics, use three repeats and fixed degree-20 indexed graphs, and verify expected "
                       "scores for every generated node. [D11]", "small")
        self.paragraph("Memory is cumulative process high-water RSS, including constructed inputs and prior result "
                       "objects; it is not per-call peak allocation. Times depend on this environment and do not prove "
                       "a speedup over the old executable, which was not used as a benchmark or correctness oracle. "
                       "The measurements support practicality within the tested input sizes. [D11]", "small")

    def discussion(self):
        self.heading("23  Course-grounded interpretation")
        self.sub("Implemented structure, intended design and drift")
        self.paragraph("This is architecture reconstruction by reverse engineering: a lower-level static dependency "
                       "graph is converted into a higher-level decomposition. The architecture-evolution lecture "
                       "distinguishes implemented, intended and described architecture, as well as static and dynamic "
                       "views. Our partitions are candidate views of the implementation. Demonstrating erosion would "
                       "require an intended design constraint and evidence that changes violate it. MQ trends alone "
                       "do not provide that evidence. [L5 PDF pp.9,12,14,18–19]")
        self.sub("Lehman's laws are a lens, not an automatic conclusion")
        self.paragraph("Changes in class counts and dependencies are consistent with continuing change and may "
                       "motivate inspection of structural complexity. They cannot by themselves verify continuing "
                       "functional growth, declining user-perceived quality, invariant effort or organizational "
                       "stability. Those claims need requirements, usage, effort and process evidence. The lectures "
                       "also restrict the empirical laws to E-type systems; a Java utility library should not be "
                       "classified as E-type without explaining its real-world adaptation context. [L12 pp.33–48]")
        self.sub("Operational definitions and traceability")
        self.paragraph("The requirements lectures emphasize ambiguity, measurable statements and traceability. "
                       "“Internal,” “class,” “dependency,” “stable release,” “omnipresent” and “quality” therefore have "
                       "explicit operational definitions here. The same term can mean something different in "
                       "requirements relationships, runtime interactions and class-file structure. Stored inputs, "
                       "parameters and per-cluster terms make a claim auditable, but traceability alone does not "
                       "guarantee its correctness. [L3 pp.9–19,27–33; L4 pp.11–15]")
        self.sub("Material limits of this experiment")
        self.paragraph("The 30 observations form a systematic sparse sample, not a random sample or a complete history. "
                       "The artifact and namespace boundary omits external interactions and other modules. Static "
                       "analysis cannot observe every reflective or dynamically created dependency. Published bytecode "
                       "can reflect different compiler versions and inlining. The UE replacement depends on resolved "
                       "member usage and its fixed thresholds; it is not interchangeable with the older Noise method. "
                       "ACDC granularity and KMeans' geometry/pilot extrapolation affect the recovered structure. [D2; D4; D6; D7]")
        coverage = self.d.ue_cases["resolution_coverage"]
        self.paragraph(f"The latest extraction records {coverage['unresolved_event_rows']} unresolved member-use events "
                       f"({coverage['distinct_recorded_references']} distinct recorded references); "
                       f"{coverage['unresolved_interclass_event_rows_after_merging']} events cross normalized class boundaries. "
                       "These diagnostics quantify a known evidence gap. Their ratio to raw observed calls includes "
                       "external and intraclass events, so it is not a completeness or false-negative rate. [D14]", "small")
        self.paragraph("Automated metrics remove repeated manual calculation, but they do not remove modeling "
                       "judgment. Without an expert architecture, partition agreement is not accuracy. The AI output "
                       "adds a semantic interpretation and its own prompt/model constraints. The defensible conclusions "
                       "are the observed structural results under these declared choices. [AS pp.3–4; L3 pp.16–19]", "small")

    def reproduction(self):
        d = self.d
        self.heading("24  Reproduce and audit the study")
        self.paragraph("Use the repository's pinned Python dependencies and Java toolchain instructions first. The "
                       "following sequence reconstructs the data-to-report chain; --offline verifies an existing artifact "
                       "cache. Exact flags and prerequisites are documented in the repository README and acquisition guide.")
        self.formula("<font name='Mono' size='8.3'>python scripts/unpack_data.py<br/>"
                     "python scripts/select_versions.py --check<br/>"
                     "python scripts/fetch_data.py --offline<br/>"
                     "python scripts/fetch_tools.py<br/>"
                     "python scripts/build_java.py<br/>"
                     "python scripts/run_study.py --phase all<br/>"
                     "python scripts/audit_change_points.py<br/>"
                     "python scripts/audit_revision.py<br/>"
                     "python scripts/evaluate_ai.py<br/>"
                     "python scripts/validate_results.py<br/>"
                     "python scripts/build_report.py</font>")
        self.table(["Artifact path", "What to verify"], [
            ["config/versions.json", "30 distinct families with immutable representatives, URLs, hashes and catalog decisions."],
            ["data/graphs/&lt;version&gt;/", "Original instructor input/raw output; normalization; typed and binary edges; aliases; separate supplemental member evidence and comparisons."],
            ["results/versions/&lt;version&gt;/", "UE scores, retained graph, exactly one A1–A4 assignment and its execution/quality details."],
            ["results/*.csv", "30 size rows, 120 metric rows, 60 same-graph rows, 29 transitions, 180 stage timings, 178 directional comparison pairs."],
            ["results/run_manifest.json", "Input/config hashes, algorithm-source hashes, Python, Java and package versions."],
            ["results/ai/", "Actual AI prompts, provided input, output, coverage audit and comparison."],
            ["report/report_manifest.json", "Hashes of files read by the report and generated PDF/figures; no recomputed partitions."],
        ], [195, WIDTH - 195], small=True)
        package_line = "; ".join(f"{name} {version}" for name, version in d.run["packages"].items())
        self.paragraph(f"Recorded software: Python {esc(d.run['python'].split()[0])}; {esc(package_line)}. "
                       "The full Java toolchain identity and operating-system string are retained in run_manifest.json. "
                       "Stable inputs, ordering and seeds make the procedure repeatable; environment changes can still "
                       "affect floating-point details and wall time. [D11]", "small")
        self.paragraph("Selection SHA-256: " + esc(d.run["manifest_sha256"]) + "<br/>"
                       "Configuration SHA-256: " + esc(d.run["config_sha256"]), "mono")
        self.paragraph("The published repository packages raw artifacts and full per-release graph/result evidence "
                       "in deterministic ZIP bundles under archives/versions. Unpacking restores the documented paths; "
                       "summaries, source code, figures and guides remain directly readable. No source artifact is "
                       "replaced by a derived summary.", "small")
        audit = read_json(ROOT / "results/validation.json")
        if audit["status"] != "passed" or audit["failure_count"]:
            raise ValueError("The final report requires a passed independent result audit")
        self.paragraph(f"Independent audit status: <b>{esc(audit['status'])}</b>, {count(audit['checks_performed'])} "
                       f"evidence checks and {audit['failure_count']} failures. "
                       "A separate standard-library implementation recalculates exact-rational UE, lecture MQ and "
                       "contingency-table ARI and directional MoJoFM from stored evidence. It checks all 120 final "
                       "partitions, all 14 pilot inertias and the fixed AI output. This establishes "
                       "internal consistency, not completeness of static analysis or intended-design accuracy. [D13]", "small")

    def metric_appendix(self):
        d = self.d
        for page in range(3):
            subset = d.names[page * 10:(page + 1) * 10]
            self.heading(f"Appendix A{page + 1}  Complete quality results")
            self.paragraph(f"Selected releases {page * 10 + 1}–{page * 10 + 10} of 30. Each row is the only final "
                           "partition for that release and condition. Full precision and per-cluster/pair terms are "
                           "stored in the result artifacts. [D1; D9]", "small")
            rows = []
            for v in subset:
                for c in CONDITIONS:
                    r = d.by_metric[v, c]
                    rows.append([v, c, str(integer(r, "n_nodes")), str(integer(r, "n_clusters")),
                                 fmt(number(r, "cohesion"), 4), fmt(number(r, "coupling"), 4), fmt(number(r, "mq"), 4),
                                 percent(number(r, "inter_edge_fraction"), 0), str(integer(r, "max_cluster_size"))])
            self.table(["Release", "Run", "N", "k", "Cohesion", "Coupling", "MQ", "Inter %", "Largest"], rows,
                       [55, 34, 40, 34, 73, 73, 70, 58, WIDTH - 437], small=True,
                       numeric=(2, 3, 4, 5, 6, 7, 8), padding=3.1)
            self.paragraph("N: evaluated nodes. k: nonempty clusters. Inter %: percentage of graph edges that cross "
                           "clusters. Largest: maximum cluster size. A1=ACDC/full; A2=ACDC/UE filtered; "
                           "A3=KMeans/full; A4=KMeans/UE filtered. Rounded displayed terms can differ in their "
                           "last digit from subtracting rounded cohesion and coupling.", "tiny")

    def references(self):
        self.heading("References and source index")
        self.sub("Supplied teaching material")
        refs = [
            ("AS", "EPL484, Fall 2026, Project 1 instructions, 5 PDF pages. Eligibility p.1; data pp.2–3; AI and report pp.3–5."),
            ("TUT", "Project 1 tutorial, 12 PDF pages. Deadline p.2; relation types p.6; ACDC pp.7–8; clustering pp.10–12."),
            ("L12", "Lectures 1–2: Introduction, 50 PDF pages. Evolution, maintenance and S/P/E classification pp.15–33; Lehman's laws and limits pp.35–48."),
            ("L3", "Lecture 3: Requirements, Part 1, 38 PDF pages. Measurable definitions/automation pp.9–19; relationship and traceability models pp.27–33."),
            ("L4", "Lecture 4: Requirements, Part 2, 33 PDF pages. Traceability and its limits pp.11–15; feedback evidence pp.22–31."),
            ("L5", "Lecture 5: Architecture Evolution, 34 PDF pages. PDF p.9 = printed slide10; after the missing slide6, PDF and printed numbers differ by one."),
            ("L67", "Lectures 6–7: Architecture Reconstruction, 50 PDF pages. MQ equations and worked example pp.15–17; ACDC pp.19–24; older Noise method pp.46–47."),
        ]
        for key, value in refs:
            self.paragraph(f"<b>[{key}]</b> {esc(value)}", "tiny")
        self.sub("Research and primary documentation")
        webrefs = [
            ("UE", "Yano and Matsuo (2020), Moderate Detection and Removal of Omnipresent Modules in Software Clustering, ICSME, pp.662–666. Equations1–3: p.663; procedure: p.664.", "https://doi.org/10.1109/ICSME46990.2020.00068"),
            ("NOISE", "Constantinou, Kakarontzas and Stamelos (2015), JSS107, pp.142–157. Older significance-based method, distinguished from this UE replacement.", "https://doi.org/10.1016/j.jss.2015.05.065"),
            ("ACDC", "Original ACDC author archive, preserved and SHA-256 pinned in third_party/acdc.", "https://www.eecs.yorku.ca/~bil/downloads/acdc.tar"),
            ("SK", "scikit-learn 1.8 KMeans API and normalize API; actual installed version is recorded by the run.", "https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html"),
            ("JVMS", "Java Virtual Machine Specification21, §5.4.3.2–5.4.3.4: field and method resolution.", "https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html"),
            ("G1", "Guava source repository and project overview.", "https://github.com/google/guava"),
            ("G2", "Guava ReleaseHistory, with linked historical release notes.", "https://github.com/google/guava/wiki/ReleaseHistory"),
        ]
        for key, description, url in webrefs:
            self.paragraph(f"<b>[{key}]</b> {esc(description)} "
                           f"<link href='{esc(url)}' color='#247D72'>{esc(url)}</link>", "tiny")
        self.sub("Repository evidence cited in this report")
        evidence = [
            ("D1", "results/sizes.csv; metrics.csv; versions/*/*_metrics.json"),
            ("D2", "docs/omnipresent.md; src/evolution/omnipresent.py; results/versions/*/ue.json"),
            ("D3", "results/same_graph_comparisons.csv; versions/*/*_projected_to_retained_metrics.json"),
            ("D4", "docs/project_selection.md; config/versions.json; data/provenance/tag_inventory.json; project_eligibility.json"),
            ("D5", "docs/data_acquisition.md; scripts/fetch_data.py; data/provenance/acquisition.json and source/Git audits"),
            ("D6", "docs/modeling_decisions.md; extractor source; data/graphs/*/provenance.json and diagnostics"),
            ("D7", "docs/course_traceability.md; src/evolution/clustering.py; config/analysis.json; A1–A4 run metadata"),
            ("D8", "results/pilot/pilot.json and associated pilot assignments"),
            ("D9", "src/evolution/metrics.py; tests; results/versions/*/*_quality/"),
            ("D10", "results/evolution.csv; canonical class and edge manifests"),
            ("D11", "results/runtimes.csv; run_manifest.json; performance/ue_benchmark.json"),
            ("D12", "results/ai/experiment.json and its exact prompt/input/output/quality artifacts"),
            ("D13", "scripts/validate_results.py; results/validation.json, independent artifact audit"),
            ("D14", "docs/ue_case_study.md; results/performance/case_checks.json, exact-fraction source-backed UE cases"),
            ("D15", "scripts/audit_change_points.py; results/change_points.json, source and graph-difference audit"),
            ("D16", "docs/mojofm.md; src/evolution/mojofm.py; saved directional partition agreement tables"),
            ("D17", "results/baseline_v1; original full study at Git commit d970305; revised config and primary extractor comparison"),
        ]
        for key, value in evidence:
            self.paragraph(f"<b>[{key}]</b> {esc(value)}", "tiny")

    def build(self, path):
        self.cover()
        self.revision()
        self.executive()
        self.selection()
        self.provenance()
        self.structural_model()
        self.ue_method()
        self.recovery_methods()
        self.pilot()
        self.quality()
        self.growth()
        self.metadata_breakdown()
        self.release_table()
        self.removals()
        self.mq_results()
        self.components()
        self.same_graph_results()
        self.agreement_results()
        self.granularity()
        self.temporal()
        self.change_evidence()
        self.cluster_profiles()
        self.ai_sections()
        self.performance()
        self.discussion()
        self.reproduction()
        self.metric_appendix()
        self.references()
        ReportDoc(path).build(self.story)


def render_qa(pdf_path, qa_dir):
    """Render every page; return machine-checkable page/text geometry evidence."""
    import fitz
    qa_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False)
        image_path = qa_dir / f"page_{i + 1:02d}.png"
        pixmap.save(image_path)
        blocks = page.get_text("dict")["blocks"]
        outside = []
        for block in blocks:
            if block.get("type") != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            if x0 < 0 or y0 < 0 or x1 > page.rect.width + .5 or y1 > page.rect.height + .5:
                outside.append([round(v, 2) for v in block["bbox"]])
        pages.append({"page": i + 1, "text_characters": len(page.get_text()),
                      "render": str(image_path.relative_to(ROOT)), "out_of_page_text_blocks": outside})
    result = {"pdf": str(pdf_path.relative_to(ROOT)), "pdf_sha256": sha256(pdf_path), "page_count": len(doc), "pages": pages,
              "all_pages_rendered": True, "visual_inspection": "Render files must be visually reviewed; geometry checks alone do not establish layout quality."}
    (REPORT / "render_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT / "guava_evolution_report_revised.pdf")
    parser.add_argument("--render-qa", action="store_true", help="Render every PDF page using PyMuPDF")
    args = parser.parse_args()
    data = StudyData()
    REPORT.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    setup_fonts()
    rl_config.invariant = 1
    make_figures(data)
    builder = ReportBuilder(data)
    builder.build(args.output)
    canonical = REPORT / "guava_evolution_report.pdf"
    if args.output.resolve() != canonical.resolve():
        shutil.copyfile(args.output, canonical)
    figures = sorted(FIGURES.glob("*.png")) + sorted(FIGURES.glob("*.svg"))
    manifest = {
        "report": str(args.output.relative_to(ROOT)), "report_sha256": sha256(args.output),
        "generator": "scripts/build_report.py", "generator_sha256": sha256(Path(__file__)),
        "packages": {name: importlib.metadata.version(name) for name in ("reportlab", "matplotlib", "numpy")},
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(set(data.inputs) | READ_INPUTS)},
        "method_sources": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(
            list((ROOT / "src/evolution").glob("*.py")) + list((ROOT / "docs").glob("*.md"))
            + [ROOT / "java/DependencyExtractor.java", ROOT / "scripts/fetch_data.py"]
        )},
        "figures": {str(p.relative_to(ROOT)): sha256(p) for p in figures},
        "sections": builder.sections,
        "study_revision": 2, "architecture_count": 120, "metric_appendix_rows": 120,
        "canonical_copy": str(canonical.relative_to(ROOT)), "canonical_copy_sha256": sha256(canonical),
        "ai_experiment_present": (data.ai_dir / "experiment.json").exists(),
        "policy": "Read saved results only; fail on missing required classical results or stale config hashes; no new partitions generated.",
    }
    (REPORT / "report_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    result = {"report": str(args.output), "bytes": args.output.stat().st_size,
              "figures": len(figures), "ai_experiment_present": manifest["ai_experiment_present"]}
    if args.render_qa:
        result["page_count"] = render_qa(args.output, REPORT / "qa")["page_count"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
