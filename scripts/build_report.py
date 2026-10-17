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
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "results/figures"
REPORT = ROOT / "report"
VECTOR_FIGURES = REPORT / "qa/vector_figures"
PAGE_W, PAGE_H = A4
MARGIN = 49
WIDTH = PAGE_W - 2 * MARGIN
INK = "#111111"
MID_GRAY = "#555555"
LIGHT_GRAY = "#777777"
MUTED = "#333333"
PALE = "#F2F2F2"
CONDITIONS = ("A1", "A2", "A3", "A4")
CONDITION_LABELS = {
    "A1": "A1: ACDC, full", "A2": "A2: ACDC, filtered",
    "A3": "A3: k-means, full", "A4": "A4: k-means, filtered",
}
LINE_STYLES = {
    "A1": dict(color=INK, linestyle="-", marker="o"),
    "A2": dict(color=INK, linestyle="--", marker="s", markerfacecolor="white"),
    "A3": dict(color=LIGHT_GRAY, linestyle="-.", marker="^"),
    "A4": dict(color=LIGHT_GRAY, linestyle=":", marker="D", markerfacecolor="white"),
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
    names = {"Body": "DejaVuSerif.ttf", "Body-Bold": "DejaVuSerif-Bold.ttf",
             "Body-Italic": "DejaVuSerif-Italic.ttf", "Mono": "DejaVuSansMono.ttf",
             "Sans": "DejaVuSans.ttf", "Sans-Bold": "DejaVuSans-Bold.ttf",
             "Title": "DejaVuSerif.ttf", "Title-Bold": "DejaVuSerif-Bold.ttf"}
    for name, filename in names.items():
        path = font_root / filename
        if not path.exists():
            raise FileNotFoundError(f"Matplotlib's bundled DejaVu font is missing: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-Bold")
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")
    pdfmetrics.registerFontFamily("Title", normal="Title", bold="Title-Bold", italic="Title", boldItalic="Title-Bold")


def configure_plots():
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "font.size": 9, "axes.titlesize": 11,
        "axes.labelsize": 9, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": False,
        "axes.grid": True, "grid.color": "#DDDDDD", "grid.alpha": 0.8,
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
    VECTOR_FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(VECTOR_FIGURES / f"{name}.pdf", bbox_inches="tight",
                metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def make_figures(data):
    FIGURES.mkdir(parents=True, exist_ok=True)
    configure_plots()
    x = np.arange(len(data.names))
    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.8), sharex=True, constrained_layout=True)
    for ax, key, label, color in zip(axes, ("classes", "dependencies"),
                                    ("Canonical internal classes", "Directed internal dependencies"), (MID_GRAY, INK)):
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
    axes[0].bar(x, [integer(r, "omnipresent_classes") for r in data.sizes], color=MID_GRAY, width=.7)
    axes[0].set_ylabel("UE-removed classes")
    axes[1].plot(x, [100 * (1 - number(r, "edge_retention_fraction")) for r in data.sizes],
                 color=LIGHT_GRAY, marker="o", markersize=3, linewidth=1.5)
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
    for full, color, shift, label in [("A1", "#222222", -.19, "ACDC: A2 − projected A1"),
                                      ("A3", LIGHT_GRAY, .19, "KMeans: A4 − projected A3")]:
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
    axes[0].bar(tx, [integer(r, "added_classes") for r in data.evolution], color=MID_GRAY, label="Added identities")
    axes[0].bar(tx, [-integer(r, "removed_classes") for r in data.evolution], color=LIGHT_GRAY, label="Removed identities")
    axes[0].set_ylabel("Class identity changes")
    axes[0].axhline(0, color=MUTED, linewidth=.7)
    axes[0].legend(ncol=2, fontsize=8)
    for key, label, color, style in [("common_node_edge_jaccard", "Edge Jaccard", MID_GRAY, "-"),
                                    ("acdc_adjusted_rand", "ACDC partition ARI", "#222222", "--"),
                                    ("kmeans_adjusted_rand", "KMeans partition ARI", LIGHT_GRAY, "-.")]:
        axes[1].plot(tx, [number(r, key) for r in data.evolution], label=label, color=color,
                     linestyle=style, marker="o", markersize=3, linewidth=1.3)
    axes[1].set_ylabel("Agreement on common identities")
    axes[1].set_ylim(-.05, 1.05)
    axes[1].legend(ncol=3, fontsize=7.5)
    sample_ticks(axes[1], data)
    save_figure(fig, "07_temporal_change")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.1), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.1, 1]})
    stages = ["extraction", "UE", "A1", "A2", "A3", "A4"]
    stage_times = {s: [number(r, "seconds") for r in data.runtimes if r["stage"] == s] for s in stages}
    axes[0].barh(stages[::-1], [statistics.median(stage_times[s]) for s in stages[::-1]], color=MID_GRAY)
    axes[0].set_xlabel("Median seconds per release")
    axes[0].set_title("Recorded study stages")
    cases = data.benchmark["cases"]
    axes[1].plot([c["distinct_member_references"] / 1000 for c in cases],
                 [c["median_seconds"] for c in cases], color=LIGHT_GRAY, marker="o", linewidth=1.7)
    axes[1].set_xlabel("Distinct member references (thousands)")
    axes[1].set_ylabel("Median seconds, 3 repeats")
    axes[1].set_title("UE detector synthetic scaling")
    axes[1].set_ylim(bottom=0)
    save_figure(fig, "08_performance")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 4.9), sharex=True, constrained_layout=True)
    axes[0].plot(x, [r["annotations"] for r in data.class_breakdown], color=MID_GRAY, marker="o", markersize=3)
    axes[0].set_ylabel("Owned annotation types")
    axes[0].set_ylim(bottom=0)
    axes[1].plot(x, [r["isolates"] for r in data.class_breakdown], color=INK, marker="o", markersize=3, label="All isolates")
    axes[1].plot(x, [r["annotation_isolates"] for r in data.class_breakdown], color=LIGHT_GRAY, marker="s", markersize=3, linestyle="--", label="Annotation isolates")
    axes[1].set_ylabel("Primary-graph isolated types")
    axes[1].set_ylim(bottom=0)
    axes[1].legend(fontsize=8)
    sample_ticks(axes[1], data)
    save_figure(fig, "09_metadata_isolates")

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.3), constrained_layout=True)
    curve = data.calibration["selection"]["curve"]
    chosen = data.calibration["pilot_k"]
    axes[0].plot([r["k"] for r in curve], [r["inertia"] for r in curve], color=MID_GRAY, marker="o", markersize=3)
    axes[0].axvline(chosen, color=LIGHT_GRAY, linestyle="--", label=f"Selected k={chosen}")
    axes[0].set_xlabel("Candidate k on pilot only")
    axes[0].set_ylabel("Within-cluster squared-distance inertia")
    axes[0].legend(fontsize=8)
    axes[1].plot([r["k"] for r in curve], [r["chord_gap"] for r in curve], color=INK, marker="o", markersize=3)
    axes[1].axvline(chosen, color=LIGHT_GRAY, linestyle="--")
    axes[1].axhline(data.calibration["selection"]["minimum_gap"], color=MUTED, linewidth=.8, linestyle=":")
    axes[1].set_xlabel("Candidate k")
    axes[1].set_ylabel("Normalized gap below endpoint chord")
    save_figure(fig, "10_k_pilot")

    fig, axes = plt.subplots(2, 1, figsize=(7.6, 5.0), sharex=True, constrained_layout=True)
    for ax, full, label, color in zip(axes, ("A1", "A3"), ("ACDC", "KMeans"), (MID_GRAY, LIGHT_GRAY)):
        rows = data.comparison(full)
        ax.plot(x, [number(r, "mojofm_full_to_filtered") for r in rows], color=color, marker="o", markersize=3, label="Projected full → filtered")
        ax.plot(x, [number(r, "mojofm_filtered_to_full") for r in rows], color=color, marker="s", markersize=3, linestyle="--", label="Filtered → projected full")
        ax.set_ylabel(label + " MoJoFM (0–100)")
        ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
    sample_ticks(axes[-1], data)
    save_figure(fig, "11_mojofm")


class VectorFigure(Flowable):
    """Reserve the chart's layout box and record where its vector PDF belongs."""

    def __init__(self, name, width, height, placements):
        super().__init__()
        self.name, self.width, self.height = name, width, height
        self.placements = placements

    def draw(self):
        x, y = self.canv.absolutePosition(0, 0)
        self.placements.append({"name": self.name, "page": self.canv.getPageNumber(),
                                "rect": (x, PAGE_H - y - self.height, x + self.width, PAGE_H - y)})


def embed_vector_figures(path, placements):
    """Insert Matplotlib's vector exports without changing text or page layout."""
    import fitz
    path = Path(path)
    temporary = path.with_suffix(".vector.tmp.pdf")
    with fitz.open(path) as report:
        for item in placements:
            with fitz.open(VECTOR_FIGURES / f"{item['name']}.pdf") as figure:
                report[item["page"] - 1].show_pdf_page(fitz.Rect(item["rect"]), figure, 0,
                                                       keep_proportion=False)
        report.save(temporary, garbage=4, deflate=True, no_new_id=True)
    temporary.replace(path)


class ReportDoc(BaseDocTemplate):
    def __init__(self, path, figure_placements):
        super().__init__(str(path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=57, bottomMargin=48, title="Guava: Software Evolution and Architecture Recovery",
                         author="EPL484 project study", subject="Thirty stable releases; ACDC, KMeans and Usage Equality",
                         creator="Reproducible ReportLab report generator", pageCompression=1)
        frame = Frame(MARGIN, 48, WIDTH, PAGE_H - 105, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0, id="normal")
        self.addPageTemplates(PageTemplate(id="normal", frames=[frame], onPage=self.decorate))
        self.figure_placements = figure_placements

    def beforeDocument(self):
        self.figure_placements.clear()

    def decorate(self, canvas, doc):
        canvas.saveState()
        if doc.page > 1:
            canvas.setFont("Body", 7.5)
            canvas.setFillColor(colors.HexColor(MUTED))
            canvas.drawString(MARGIN, PAGE_H - 29, "Guava: software evolution and architecture recovery")
            canvas.setStrokeColor(colors.HexColor("#BBBBBB"))
            canvas.line(MARGIN, PAGE_H - 37, PAGE_W - MARGIN, PAGE_H - 37)
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(MARGIN, 27, "EPL484 · Project 1")
        canvas.drawRightString(PAGE_W - MARGIN, 27, str(doc.page))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "_bookmark_key"):
            key = flowable._bookmark_key
            level = 0 if flowable.style.name == "Chapter" else 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level, False)
            if level == 0:
                self.notify("TOCEntry", (0, flowable.getPlainText(), self.page, key))


class ReportBuilder:
    def __init__(self, data):
        self.d = data
        self.styles = {
            "body": ParagraphStyle("BodyText", fontName="Body", fontSize=10.5, leading=15,
                                   textColor=colors.HexColor(INK), spaceAfter=7, allowWidows=0, allowOrphans=0),
            "small": ParagraphStyle("Small", fontName="Body", fontSize=9, leading=12.5,
                                    textColor=colors.HexColor(MUTED), spaceAfter=6, allowWidows=0, allowOrphans=0),
            "tiny": ParagraphStyle("Tiny", fontName="Body", fontSize=8.1, leading=11.5,
                                   textColor=colors.HexColor(MUTED), spaceAfter=5),
            "chapter": ParagraphStyle("Chapter", fontName="Title-Bold", fontSize=18, leading=24,
                                      textColor=colors.HexColor(INK), spaceAfter=17, keepWithNext=1),
            "contents": ParagraphStyle("ContentsTitle", fontName="Title-Bold", fontSize=18, leading=24,
                                      textColor=colors.HexColor(INK), spaceAfter=17, keepWithNext=1),
            "section": ParagraphStyle("Section", fontName="Body-Bold", fontSize=13, leading=18,
                                      textColor=colors.HexColor(INK), spaceBefore=15, spaceAfter=9, keepWithNext=1),
            "sub": ParagraphStyle("Subhead", fontName="Body-Bold", fontSize=10.8, leading=15,
                                  textColor=colors.HexColor(INK), spaceBefore=8, spaceAfter=6, keepWithNext=1),
            "caption": ParagraphStyle("Caption", fontName="Body", fontSize=8.7, leading=12.2,
                                      textColor=colors.HexColor(MUTED), spaceAfter=11),
            "cell": ParagraphStyle("Cell", fontName="Sans", fontSize=8.3, leading=11.2,
                                   textColor=colors.HexColor(INK)),
            "cell_small": ParagraphStyle("CellSmall", fontName="Sans", fontSize=7.8, leading=10.6,
                                         textColor=colors.HexColor(INK)),
            "header": ParagraphStyle("Header", fontName="Sans-Bold", fontSize=8, leading=10.8,
                                     textColor=colors.HexColor(INK)),
            "mono": ParagraphStyle("Mono", fontName="Mono", fontSize=8.2, leading=12,
                                   textColor=colors.HexColor(INK), spaceAfter=8, splitLongWords=1),
            "cover": ParagraphStyle("Cover", fontName="Title-Bold", fontSize=24, leading=32,
                                    textColor=colors.HexColor(INK), spaceAfter=19),
        }
        self.story = []
        self.sections = []
        self.chapter_count = 0
        self.chapter_label = ""
        self.subsection_count = 0
        self.figure_count = 0
        self.figure_placements = []

    def paragraph(self, text, style="body"):
        self.story.append(Paragraph(text, self.styles[style]))

    def chapter(self, title, label=None):
        if self.story:
            self.story.append(PageBreak())
        if label is None:
            self.chapter_count += 1
            label = str(self.chapter_count)
        self.chapter_label = label
        self.subsection_count = 0
        if label:
            title = (f"Appendix {label}. " if label.isalpha() else f"{label}. ") + title
        self._numbered_heading(title, "chapter")

    def _numbered_heading(self, title, style):
        paragraph = Paragraph(title, self.styles[style])
        paragraph._bookmark_key = f"section-{len(self.sections)}"
        self.sections.append(title)
        self.story.append(paragraph)

    def heading(self, title):
        self.subsection_count += 1
        title = re.sub(r"^\d+\s+", "", title)
        prefix = f"{self.chapter_label}.{self.subsection_count}  " if self.chapter_label else ""
        self._numbered_heading(prefix + title, "section")

    def contents(self):
        self.story.append(PageBreak())
        self.paragraph("Contents", "contents")
        toc = TableOfContents()
        toc.levelStyles = [ParagraphStyle("TOC", fontName="Body", fontSize=10.5, leading=15,
                                         textColor=colors.HexColor(INK), spaceBefore=10,
                                         leftIndent=0, firstLineIndent=0, rightIndent=20)]
        toc.dotsMinLevel = 0
        self.story.append(toc)
        self.story.append(Spacer(1, 23))
        self.sub("How to read the report")
        self.paragraph("Section 1 gives the purpose and main findings. Sections 2 and 3 explain how the data "
                       "was obtained and how the experiments work. Sections 4 and 5 present the evolution and "
                       "clustering results; Sections 6 and 7 discuss the AI proposal and what the results mean.")
        self.paragraph("The reproduction commands are in Section 8. The appendices contain every selected release, "
                       "all 120 final quality measurements, and the changes from the earlier study. Citations such "
                       "as [L67] refer to the supplied lectures; [D1] and similar labels point to saved repository "
                       "evidence. The reference list gives their full names and paths.", "small")

    def sub(self, title):
        self.paragraph(title, "sub")

    def table(self, headers, rows, widths=None, small=False, numeric=(), padding=5):
        style = self.styles["cell_small" if small else "cell"]
        values = [[Paragraph(esc(v), self.styles["header"]) for v in headers]]
        values.extend([[Paragraph(str(v), style) for v in row] for row in rows])
        table = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
        commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), padding),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
            ("LINEABOVE", (0, 0), (-1, 0), .6, colors.HexColor(INK)),
            ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor(MUTED)),
            ("LINEBELOW", (0, -1), (-1, -1), .4, colors.HexColor("#999999")),
        ]
        for row in range(1, len(values)):
            if row % 2 == 0:
                commands.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor(PALE)))
        # Paragraph alignment must also be set for genuinely right-aligned text.
        for column in numeric:
            for row in range(1, len(values)):
                values[row][column].style = ParagraphStyle("NumericCell", parent=style, alignment=TA_RIGHT)
        table.setStyle(TableStyle(commands))
        self._keep_previous_paragraph()
        self.story.append(table)
        self.story.append(Spacer(1, 9))

    def _keep_previous_paragraph(self):
        if self.story and isinstance(self.story[-1], Paragraph):
            paragraph = self.story[-1]
            if paragraph.style.name in {"BodyText", "Small", "Tiny", "Subhead"}:
                paragraph.style = ParagraphStyle("WithFollowing", parent=paragraph.style, keepWithNext=1)

    def chart(self, name, height=None, caption=""):
        image = Image(str(FIGURES / f"{name}.png"))
        ratio = image.imageHeight / image.imageWidth
        image.drawWidth = WIDTH
        image.drawHeight = WIDTH * ratio if height is None else height
        self.figure_count += 1
        block = [VectorFigure(name, image.drawWidth, image.drawHeight, self.figure_placements)]
        if caption:
            caption = re.sub(r"^Figure \d+\.", f"Figure {self.figure_count}.", caption)
            block.append(Paragraph(caption, self.styles["caption"]))
        self._keep_previous_paragraph()
        self.story.append(KeepTogether(block))

    def formula(self, text):
        cell = Paragraph(text, ParagraphStyle("Formula", parent=self.styles["body"],
                                              fontSize=10.3, leading=17, spaceAfter=0))
        table = Table([[cell]], colWidths=[WIDTH])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F6F6")),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 12),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                                   ("TOPPADDING", (0, 0), (-1, -1), 10),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        self.story.extend([table, Spacer(1, 11)])

    def cover(self):
        d = self.d
        self.story.append(Spacer(1, 30))
        self.paragraph("EPL484 · Software Evolution · Project 1", "small")
        self.story.append(Spacer(1, 15))
        self.paragraph("Guava: software evolution<br/>and architecture recovery", "cover")
        self.paragraph("A study of 30 stable releases, from 10.0 to 33.7.2")
        self.story.append(Spacer(1, 27))
        self.sub("Abstract")
        self.paragraph("This study examines how Guava's internal class structure changes over time and how two "
                       "clustering methods recover groups of related classes. Thirty releases are sampled across "
                       "the project's history. The instructor's DependencyExtractor supplies the class dependencies; "
                       "external libraries are excluded, and inner and anonymous classes are merged with their "
                       "enclosing classes. ACDC and k-means are each run before and after removing classes identified "
                       "by the supplied paper's Usage Equality method.")
        self.paragraph(f"The sampled graph grows from {count(integer(d.first, 'classes'))} to "
                       f"{count(integer(d.last, 'classes'))} classes and from "
                       f"{count(integer(d.first, 'dependencies'))} to {count(integer(d.last, 'dependencies'))} "
                       "dependencies. Removing widely used classes affects the recovery methods differently: "
                       "on the same retained graph, the lecture's modularization-quality score improves for k-means "
                       "in 29 of 30 releases and decreases for ACDC in all 30. These results describe the extracted "
                       "structure; they do not establish Guava's intended architecture. The report explains the "
                       "data, parameter choices and evaluation, and includes every final measurement. [D1; D3]")
        self.story.append(Spacer(1, 24))
        self.paragraph(f"Release dates: {d.versions[0]['release_date'][:10]} to {d.versions[-1]['release_date'][:10]}.<br/>"
                       f"Dataset snapshot: {d.manifest['selection_date_utc'][:10]}.<br/>"
                       'Project: <link href="https://github.com/google/guava" color="#111111">github.com/google/guava</link>.', "small")

    def revision(self):
        d = self.d
        self.heading("What changed in the revised analysis")
        self.paragraph("The revised analysis replaces the study at commit d970305. Its main change is to use the "
                       "instructor's extractor for the dependency graph. The table below records the other changes "
                       "so that the new results can be compared with the earlier ones. The original measurements "
                       "remain in results/baseline_v1 and in the repository history. [D17]")
        self.table(["Concern", "Revised decision"], [
            ["Dependency extraction", "Use the unmodified instructor extractor for the class graph. Keep the additional member extraction separate for Usage Equality."],
            ["Public-suffix ownership", "Include Guava-owned com.google.thirdparty.publicsuffix implementation, alongside com.google.common."],
            ["Repeated patch families", "Select 30 distinct major/minor families from 45; one stable representative per family."],
            ["Choosing k for k-means", "Choose k from an inertia elbow on one middle release, then scale it with class count using the same rule for every release."],
            ["Evaluation", "Add the lecture's directional MoJoFM measure; retain ARI as a supplementary measure and use the lecture's MQ formula without self-loops."],
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
        self.paragraph("Sampling, class scope, extraction and the k rule changed together. A difference between "
                       "the two studies' overall scores therefore cannot be attributed to one of those choices. "
                       "The extractor comparison above is narrower: it holds the release and class scope fixed "
                       "and compares the recorded edges. [D17]", "small")

    def executive(self):
        d = self.d
        self.heading("1  Introduction")
        self.paragraph("This study follows Guava through 30 releases to examine how its structure changes and how "
                       "that structure can be divided into modules. It asks how class and dependency counts develop "
                       "over time, and whether removing widely used classes helps clustering algorithms recover "
                       "more cohesive groups. Inner and anonymous classes are merged with their enclosing top-level "
                       "class, and external libraries are excluded. A dependency is a distinct directed relation "
                       "between two classes in this inventory. [D1; D4; D6]")
        self.paragraph("Each release is analysed with ACDC and k-means, before and after applying the paper's "
                       "Usage Equality method. This method identifies broadly used classes whose connections may "
                       "obscure subsystem boundaries. Filtering excludes their nodes and incident edges from the "
                       "analysis graph; it does not change Guava's source code. The four conditions are labelled "
                       "A1 to A4 below. [UE; AS pp.2–4]")
        self.table(["Condition", "Algorithm", "Graph evaluated"], [
            ["A1", "ACDC (+so, -l20)", "All merged project classes"],
            ["A2", "Same ACDC configuration", "Graph after Usage Equality filtering"],
            ["A3", "k-means on normalized dependency features", "All merged project classes"],
            ["A4", "Same features and release-specific k", "Graph after Usage Equality filtering"],
        ], [55, 194, WIDTH - 249])
        self.paragraph("A pilot on one release sets the parameters. Each release then has one final partition "
                       "for each condition, keeping the four required comparisons without repeating parameter "
                       "experiments across all versions. The ten initializations inside a k-means fit produce "
                       "a single final partition. A separate AI proposal is evaluated for the latest release. [AS pp.2–4]")
        c_change = integer(d.last, "classes") / integer(d.first, "classes") - 1
        e_change = integer(d.last, "dependencies") / integer(d.first, "dependencies") - 1
        removed = [integer(r, "omnipresent_classes") for r in d.sizes]
        self.sub("Main findings")
        self.paragraph(f"Between the first and last samples, the class count rises by {percent(c_change)} and "
                       f"the dependency count by {percent(e_change)}. Usage Equality selects {min(removed)}–{max(removed)} "
                       f"classes in a release, with {len(d.removal_frequency)} distinct class names selected at "
                       "least once. The gaps between samples mean that these trends cannot identify the exact "
                       "commit responsible for a change. [D1; D2; L12 pp.35–48]")
        self.paragraph("Modularization quality (MQ) combines average cohesion within groups and coupling between "
                       "groups. To compare the effect of regrouping, both partitions are scored on the same "
                       "remaining classes and edges. The table counts the releases in which MQ changes. [D3; D9]")
        outcome_rows = []
        for full, name in (("A1", "ACDC"), ("A3", "k-means")):
            changes = [number(r, "mq_change_same_graph") for r in d.comparison(full)]
            n_positive = sum(v > 1e-12 for v in changes)
            n_negative = sum(v < -1e-12 for v in changes)
            outcome_rows.append([name, str(n_positive), str(n_negative), str(30 - n_positive - n_negative)])
        self.table(["Method", "Higher MQ", "Lower MQ", "Unchanged"], outcome_rows,
                   [WIDTH - 285, 95, 95, 95], small=True, numeric=(1, 2, 3), padding=3)
        self.paragraph("Changes within 10<super>−12</super> count as unchanged. Higher MQ describes the extracted "
                       "structure; it does not establish the architecture intended by Guava's developers. [D3; D9]", "small")
        if (d.ai_dir / "metrics.json").exists():
            ai = read_json(d.ai_dir / "metrics.json")
            self.paragraph(f"The AI proposal places the latest {ai['n_nodes']} classes into {ai['n_clusters']} "
                           f"named modules. Its MQ is {fmt(ai['mq'], 4)}, compared with "
                           f"{fmt(d.metric('A3', 'mq'), 4)} for k-means and {fmt(d.metric('A1', 'mq'), 4)} "
                           "for ACDC on the full graph. Because the AI also uses names and package documentation, "
                           "this is not a comparison of methods given identical information. [D12]")


    def selection(self):
        d = self.d
        self.heading("Guava and the release sample")
        repo = d.eligibility["repository_metadata"]
        latest_inventory = read_json(ROOT / "data/provenance" / f"source_inventory_{d.latest}.json")
        self.paragraph("The subject is <b>Guava</b>, the Java library maintained in the google/guava repository. "
                       "The analysis follows the classes shipped in its main production JAR across 30 stable releases. "
                       "Using this artifact throughout gives the study a consistent scope: it describes the library's "
                       "class architecture, while other modules in the repository fall outside the sample. [G1; D4]")
        self.table(["Course eligibility criterion", "Recorded evidence"], [
            ["Java; latest release ≥10,000 LOC", f"GitHub primary language: {esc(repo['language'])}. "
             f"{count(latest_inventory['source_owned_java_nonblank_noncomment_lines'])} nonblank, noncomment lines in owned Java sources."],
            ["GitHub repository created before 2024", esc(repo['created_at'][:10])],
            ["Not a fork; not archived", f"fork={str(repo['fork']).lower()}; archived={str(repo['archived']).lower()} at the recorded snapshot."],
            ["≥50 commits since 2024-01-01", "100 distinct qualifying commits saved as evidence that the minimum is met; this is not a count of all commits."],
            ["≥10 major/minor releases", "30 stable releases covering exactly 30 distinct major/minor families."],
        ], [185, WIDTH - 185])
        self.paragraph(f"The line count used for course eligibility includes Guava-owned package descriptors. "
                       f"The source files represented by class nodes in the dependency graph contain "
                       f"{count(integer(d.last, 'java_code_lines'))} code lines at the latest release. Both counts "
                       "exceed the requirement, but they describe slightly different sets of files. [D4; D6]", "small")
        self.sub("How the 30 releases were chosen")
        self.paragraph("The selection rule was set before examining the quality scores. Of the 124 tag references "
                       "in the saved catalog, 82 match the numeric stable-release pattern. The other 42 include "
                       "prereleases, auxiliary artifacts and alternative names, so they should not all be described "
                       "as beta releases. Excluding nine numeric releases before 10.0, the ambiguous duplicate naming "
                       "of 13.0, and two later backports to earlier release lines leaves 70 mainline candidates in "
                       "chronological order. [D4]")
        self.formula("Family rank for sample i: <b>round(i × 44 / 29)</b>, &nbsp; i = 0,…,29")
        self.paragraph("These candidates belong to 45 major/minor families. The formula above selects 30 family "
                       "positions, counting from zero, and each selected family contributes one stable release. "
                       "The representative is its highest eligible patch, except that the first family starts at "
                       "10.0. The last observation is 33.7.2. A heavily patched family therefore receives the same "
                       "weight as any other selected family. [D4]")
        self.paragraph("The sample is spread through the ordered families, rather than through equal intervals of "
                       "calendar time. Some selected families are adjacent because 30 observations cannot all skip "
                       "a family when only 45 are available. Patch releases can serve as representatives, but no "
                       "family appears twice. A release stays in the sample even if its graph matches another release "
                       "or its quality score is unexpected. Before 23.1 the study uses the plain artifact; after the "
                       "variant split it follows the JRE artifact. Android variants do not add observations. [D4]", "small")
        self.paragraph("Dates for older releases come from Guava's release-history pages; later dates use GitHub "
                       "Release publication timestamps. Git commit dates are stored separately. The repository "
                       "evidence establishes the eligibility criteria above; instructor approval is not recorded "
                       "in the available material. [AS p.1; G2; D4]", "small")


    def provenance(self):
        d = self.d
        self.heading("Where the data came from")
        self.paragraph("For each release, the dataset records the Git commit behind its tag and downloads three "
                       "files from Maven Central: the production binary JAR, the source JAR and the Project Object "
                       "Model (POM), which identifies the published artifact. The extractor reads the published "
                       "bytecode. This avoids having to rebuild every historical version and then dropping releases "
                       "whose old build tools no longer work. Downloading the data does not execute Guava code. [D4; D5]")
        self.table(["Evidence layer", "Stored and checked"], [
            ["Release identity", "Git tag name, 40-character commit SHA, publication date, the source of that date and Maven artifact coordinate."],
            ["Artifact integrity", "Pinned SHA-256 for every downloaded file; Maven SHA-1 sidecars; ZIP CRC checks; POM version/artifact identity."],
            ["Source ownership", "Per-source-file path and checksum, source-owned class inventory, SLOC definition and excluded binary entries."],
            ["Source-to-Git audit", "Every Java source-JAR file at the oldest and newest selected endpoints compared byte for byte with the pinned Git archive."],
            ["Offline reproducibility", "Cached files must match the saved checksums. A corrupt file causes a failure rather than an automatic replacement."],
        ], [120, WIDTH - 120])
        endpoints = []
        for version in (d.names[0], d.names[-1]):
            check = read_json(ROOT / "data/provenance" / f"git_source_match_{version}.json")
            endpoints.append([version, count(check["compared_java_files"]), "All byte-identical" if check["all_sources_match"] else "Mismatch", check["commit_sha"][:12]])
        self.table(["Endpoint", "Java files", "Git/source result", "Commit prefix"], endpoints,
                   [60, 65, 220, WIDTH - 345], numeric=(1,))
        self.paragraph(f"All <b>{d.acquisition['artifact_count']} files</b> ({d.acquisition['total_artifact_bytes'] / 1024**2:.2f} MiB) "
                       "matched their saved checksums and passed the checks listed above. At the first and last "
                       "releases, every Java file in the source JAR was also compared byte for byte with the pinned "
                       "Git archive. The intermediate 28 releases have saved artifact checksums and Git identities, "
                       "but did not receive that complete per-file comparison. SHA sidecars downloaded from the "
                       "same repository help detect corruption; they do not independently authenticate the publisher. "
                       "PGP signatures were not verified. [D5]")
        self.sub("Tracing a result back to its source")
        self.paragraph("A result can be explained in the oral exam by following one release through the saved files. "
                       "Its row in <font name='Mono'>config/versions.json</font> gives the tag SHA and Maven URL. "
                       "The downloaded JAR can be hashed and checked against that record. The source manifest then "
                       "shows which classes belong to Guava, and the extractor records show how those classes become "
                       "the class and dependency CSVs used for clustering. This connects a reported measurement to "
                       "the particular upstream file from which it was obtained. [L4 pp.11–15]")
        self.paragraph("The supporting files are config/versions.json; data/provenance/SHA256SUMS; acquisition.json; "
                       "source_inventory_&lt;version&gt;.json; git_source_match_10.0.json; git_source_match_33.7.2.json. "
                       "All paths are repository-relative.", "small")


    def structural_model(self):
        d = self.d
        self.heading("From Java classes to a dependency graph")
        self.paragraph("In the graph, a node represents a Guava-owned class or type, and a directed edge A→B means "
                       "that class A depends on class B. All edges used for architecture recovery come from the "
                       "instructor's unmodified DependencyExtractor. A separate pass using ASM, a Java bytecode "
                       "reader, identifies owned classes, links nested classes to their enclosing classes, and "
                       "resolves method and field references for the Usage Equality calculation. Its additional "
                       "annotation, type and declaring-owner relationships are kept out of the main graph. [TUT p.6; D6]")
        self.paragraph("The input to the instructor's extractor is a deterministically assembled JAR containing "
                       "Guava-owned base class entries. Each entry is copied byte for byte from the Maven binary, "
                       "and its checksum confirms that the class body has not changed. The original JAR is also "
                       "kept. The tool runs through its original CompCalc.MainClass with an explicit classpath "
                       "and its unchanged bundled libraries. [D6]")
        self.table(["Evidence", "Role"], [
            ["classes.csv; class_aliases.csv", "Owned common/publicsuffix types, with genuine nested, local and anonymous classes merged using enclosing-class metadata."],
            ["instructor_raw.csv", "Original seven-category output, including occurrence counts retained for auditing."],
            ["dependencies_typed.csv; dependencies.csv", "Instructor relationships reduced first to unique typed pairs, then to unique directed class pairs; self-loops and external endpoints removed."],
            ["member_dependencies.csv", "Resolved method and field references for Usage Equality. Binary member identities remain distinct when their owning classes are merged."],
            ["supplemental_dependencies.csv", "The broader graph from ASM, saved separately to examine extraction differences."],
        ], [183, WIDTH - 183], small=True)
        self.paragraph("The analysis selects all seven relations in the tutorial: EXTENDS, IMPLEMENTS, METHOD_CALL, "
                       "METHOD_PARAMETER, FIELD_REFERENCE, TYPE_USAGE and EXCEPTION_THROWS. If several occurrences "
                       "or relation types connect the same ordered pair of classes, they produce one unweighted "
                       "edge. The graph is therefore limited to the Java constructs recognized by the supplied "
                       "executable; it is not a complete account of every possible runtime interaction. [TUT p.6]")
        self.table(["Class processing", d.names[0], d.latest], [
            ["Owned binary classes before merging", count(integer(d.first, "raw_binary_classes")), count(integer(d.last, "raw_binary_classes"))],
            ["Nested/anonymous identities merged", count(integer(d.first, "merged_binary_classes")), count(integer(d.last, "merged_binary_classes"))],
            ["Canonical project-owned types", count(integer(d.first, "classes")), count(integer(d.last, "classes"))],
            ["Owned annotation types", count(d.class_breakdown[0]["annotations"]), count(d.class_breakdown[-1]["annotations"])],
            ["Primary-graph isolates", count(d.class_breakdown[0]["isolates"]), count(d.class_breakdown[-1]["isolates"])],
        ], [WIDTH - 150, 75, 75], small=True, numeric=(1, 2), padding=3.3)
        self.paragraph("Ownership determines the boundary. It includes both com.google.common and Guava's "
                       "com.google.thirdparty.publicsuffix source files. The latter carry Guava Authors headers, "
                       "so the word 'thirdparty' in the package name is not a sufficient reason to exclude them. "
                       "JDK classes, failureaccess and external libraries are excluded from both ends of every edge. "
                       "[D4; D6]", "small")
        self.paragraph("Owned annotation types are retained as nodes, even when they have no edges. Applying an "
                       "annotation does not add an edge through the supplemental pass. Likewise, an API marked "
                       "@Beta still belongs to the stable release that ships it. Module and package descriptors "
                       "and multi-release overrides are excluded. As with the rest of this static analysis, "
                       "arbitrary reflection, erased constants and full virtual-dispatch expansion are outside "
                       "its coverage. [D6]", "small")


    def ue_method(self):
        self.heading("Identifying widely used classes with Usage Equality")
        self.paragraph("A class with many callers can connect otherwise separate parts of the system and affect "
                       "the recovered groups. However, many callers alone do not establish that the class is an "
                       "omnipresent utility. Yano and Matsuo's Usage Equality (UE) method also asks whether any one "
                       "caller has a particularly strong relationship with the class's members. The replacement "
                       "tool, JNode-UE, implements this method from the supplied 2020 paper. [UE pp.663–664; D2]")
        self.paragraph("This replacement uses UE on its own. The older JNode/Noise method described in the lectures "
                       "uses ComponentRank and shortest-path significance; those rules are not part of this "
                       "implementation. The distinction matters when comparing removal sets produced by the two "
                       "methods. [L67 pp.46–47; D2]")
        self.paragraph("For a caller class A and a target class B, D<sub>M</sub>(A,B) measures the caller's dedication "
                       "to B through the members it uses. Usage equality e(B) is high when no caller has a large "
                       "dedication score. Cardinality c(B) increases with the number of caller classes. Both "
                       "thresholds must be met before B is removed. [UE pp.663–664]")
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
        self.paragraph("With c(B) ≥ 0.90, a class needs at least ten caller classes to qualify. A class with no "
                       "incoming member references has undefined scores and is retained. The calculation runs "
                       "once on the original data, and all qualifying classes are removed together. The thresholds "
                       "stay the same for every release; removal is not repeated to create a cascade. In these "
                       "definitions, 'outside B' means another Guava-owned class. External libraries never enter "
                       "the counts. The output records every score, the strongest caller and the removal decision. "
                       "[UE; D2]")
        self.sub("Why the number of callers is not enough")
        self.paragraph("Consider a utility with one operation, used by one member in each of ten caller classes. "
                       "Each caller's dedication is 1/10, giving e = c = 0.90, so the utility qualifies for removal. "
                       "Now consider a logger with one shared operation used by 21 callers. A startup class also "
                       "uses a separate initialization operation that no other class uses. Its dedication is "
                       "1/(21×2) + 1/(1×2), so e is approximately 0.476. The logger is retained because of this "
                       "stronger relationship, despite its many callers. This example illustrates the calculation; "
                       "it is not a measurement from Guava. [UE Fig.1; D2]")
        self.paragraph("The implementation groups distinct member references with sets and dictionaries and caches "
                       "the class that declares each member. It uses stable summation and an exact rational "
                       "calculation when a score lies at a threshold. The expected cost of the main aggregation "
                       "is O(R + C + N), followed by sorting for deterministic output: R is the number of unique "
                       "member references, C the number of caller-target class pairs and N the number of classes. "
                       "The method does not require all-pairs shortest paths. [D2]", "small")


    def recovery_methods(self):
        d = self.d
        self.heading("How the architectures are recovered")
        self.sub("ACDC")
        self.paragraph("ACDC groups classes by looking for structural patterns in their dependencies. The study "
                       "compiles the archived York Java implementation and runs it with "
                       "<font name='Mono'>+so -l20</font>: SubGraph Dominator runs first, followed by Orphan Adoption "
                       "to assign remaining classes. The BodyHeader pattern matches C source and header pairs, so "
                       "it provides no evidence for this Java class graph. The result uses ACDC's default fine, "
                       "flat DownInducer output. [TUT pp.7–8; L67 pp.19–24; ACDC; D7]")
        self.paragraph("The value 20 limits the SubGraph construction stage. It does not cap the size of every final "
                       "cluster: remaining orphans can end up in a larger container. Such clusters are reported as "
                       "ACDC produces them. Classes with no dependencies, called isolates, need separate handling "
                       "because the dependency-only RSF input cannot represent them. They are restored as singleton "
                       "clusters. Every other class must occur exactly once in the returned partition; invalid, "
                       "duplicate, missing or stale output causes a failure. [D7]")
        self.sub("K-means")
        self.paragraph("K-means groups classes with similar dependency patterns into k clusters. To make those "
                       "patterns comparable across releases, each class is described using the same incoming and "
                       "outgoing dependency coordinates. A is the adjacency matrix and I supplies the identity "
                       "entries; the combined rows are normalized to unit length. [D7]")
        self.formula("U = sorted union of class identities across all 30 releases<br/>"
                     "X = row-L2-normalize([A + I, (A + I)<super>T</super>])<br/>"
                     "k<sub>full</sub> = max(1, ceil(n<sub>full</sub> × k<sub>pilot</sub> / n<sub>pilot</sub>))<br/>"
                     "k<sub>filtered</sub> = min(k<sub>full</sub>, n<sub>filtered</sub>)")
        self.paragraph(f"There are {count(d.run['feature_universe_size'])} distinct class identities across the 30 "
                       f"releases, giving <b>{count(d.run['feature_dimensions'])} columns</b> after including both "
                       "dependency directions. A current class occupies one row in a sparse CSR matrix. Coordinates "
                       "for absent or removed classes are zero. The identity entries represent self-similarity only "
                       "in this feature matrix; they do not add graph edges or affect the quality calculations "
                       "directly. Package names and AI cluster labels are not used as features. [D7]")
        self.paragraph(f"The pilot on the middle release selects k={d.calibration['pilot_k']} for "
                       f"n={d.calibration['pilot_n']} classes, or approximately "
                       f"{d.calibration['target_mean_class_count']:.2f} classes per cluster. For each final release, "
                       "k is scaled in proportion to its full graph's class count. This assumes that a similar "
                       "average group size is useful across the history. It is a study design choice, rather than "
                       "a lecture theorem or a guarantee of the best architecture, and it is not chosen by "
                       "maximizing the final MQ scores. [D7; D8]")
        self.paragraph("A3 and A4 use the same k for a release, except that k cannot exceed the number of retained "
                       "classes. An empty graph uses k=0. The command-line option --k allows a separate exploratory "
                       "run, while all 120 final partitions follow the rule above. The pilot also compares the "
                       "algorithms at ACDC's cluster count to examine the effect of group size; that comparison "
                       "does not select the final k. [D8]", "small")
        self.paragraph("The k-means settings are k-means++ initialization, Lloyd updates, random_state=484, "
                       "n_init=10, max_iter=300 and tol=10<super>−4</super>, with numerical thread pools limited "
                       "to one. Class order and output labels use a fixed ordering. Each run records the actual "
                       "cluster count, convergence warnings, iteration count, inertia and library versions. "
                       "This also records cases where identical feature rows produce fewer than k clusters. [SK; D7]", "small")


    def pilot(self):
        d = self.d
        pilot, calibration = d.pilot, d.calibration
        self.heading("Choosing the parameters in one pilot")
        self.paragraph(f"The pilot uses <b>Guava {esc(pilot['version'])}</b>, the middle release in the selected "
                       "sequence. Its position determined the choice before its quality scores were inspected. "
                       "ACDC is tried with subgraph sizes 10, 20 and 40. K-means is tried on a fixed grid of k "
                       "values on this release only. These pilot runs are kept separate from the 120 final A1–A4 "
                       "architectures, whose parameters are not tuned independently for each release. [D8]")
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
        self.paragraph("The three ACDC settings produce the same required metrics on this release, so the final "
                       "runs retain the middle setting, 20. This result describes the pilot; other graphs may "
                       "respond differently to the parameter. [D8]" if same else
                       "The table shows how the ACDC results change with the subgraph-size parameter. The final "
                       "runs retain the documented +so/-l20 setting throughout. A higher MQ on this one pilot "
                       "would not by itself establish a better architecture across the full history. [D8]")
        if diagnostic:
            selected = next(t["metrics"] for t in pilot["trials"] if t["algorithm"] != "ACDC")
            acdc = next(t["metrics"] for t in acdc_trials if t["max_subgraph_size"] == 20)
            self.paragraph(f"Giving both algorithms k={diagnostic['k']} groups produces an MQ of "
                           f"{fmt(acdc['mq'], 4)} for ACDC and {fmt(diagnostic['metrics']['mq'], 4)} for k-means. "
                           f"With the elbow-selected k, k-means has MQ {fmt(selected['mq'], 4)}. Comparing these "
                           "values helps show how much cluster count matters on this graph. Equal counts do not "
                           "ensure equal size distributions or equally meaningful groups, so this diagnostic is "
                           "not used to set the final k. [D8]")
        self.heading("Reading the k-means elbow curve")
        self.paragraph("Inertia is the sum of squared distances from classes to their cluster centers. Adding "
                       "clusters generally reduces it; the elbow is a point beyond which further reductions become "
                       "smaller. The pilot uses a specified geometric rule to locate that point, as shown below. [SK; D8]")
        self.chart("10_k_pilot", caption="Figure 10. Pilot inertia and the normalized distance from the endpoint "
                   "line. The k selection uses this curve, without using MQ. Source: results/pilot/k_inertia_curve.csv.")
        selection = calibration["selection"]
        self.table(["Candidate k", "Inertia", "Normalized gap", "Decision"], [
            [str(r["k"]), fmt(r["inertia"], 4), fmt(r["chord_gap"], 4), "Selected" if r["k"] == calibration["pilot_k"] else ""]
            for r in selection["curve"]], [85, 133, 135, WIDTH - 353], small=True, numeric=(0, 1, 2), padding=3)
        self.paragraph(f"The rule normalizes x=(k−k_min)/(k_max−k_min) and "
                       f"y=(I−I_last)/(I_first−I_last), then calculates gap=1−x−y. It chooses the largest interior "
                       f"gap if that gap is at least {selection['minimum_gap']:.2f}, resolving exact ties with the "
                       "smaller k. Otherwise it uses the candidate nearest to the declared fallback, k=30. "
                       f"The recorded decision is {esc(selection['reason'])}: k={calibration['pilot_k']}, with "
                       f"maximum gap {selection['maximum_interior_gap']:.4f}. [D8]", "small")
        self.paragraph("The selected elbow is broad: neighboring candidates have similar gaps. Its position also "
                       "depends on the candidate range, the feature representation and the fitted clusters. It "
                       "indicates diminishing improvement in distance fit on this graph, rather than a known "
                       "number of true components. Scaling the chosen k by class count then carries the same "
                       "target average group size to other releases without repeating the sweep. The results "
                       "include the actual cluster sizes so that this assumption can be assessed. [D8]", "small")


    def quality(self):
        self.heading("Evaluating the recovered groups")
        self.paragraph("A useful structural grouping should bring related classes together while keeping "
                       "dependencies between groups relatively sparse. The reconstruction lecture expresses this "
                       "through modularization quality (MQ): average cohesion within clusters minus average "
                       "coupling between pairs of clusters. In this study, edges are directed and unweighted, "
                       "with no self-loops. Let n<sub>i</sub> be the number of classes in cluster i, μ<sub>i</sub> "
                       "its internal edge count, and ε<sub>ij</sub> the edges between clusters i and j, counted "
                       "in both directions. [L67 pp.15–17]")
        self.formula("cohesion<sub>i</sub> = μ<sub>i</sub> / [n<sub>i</sub>(n<sub>i</sub> − 1)] for n<sub>i</sub> &gt; 1; otherwise 0<br/>"
                     "coupling<sub>ij</sub> = ε<sub>ij</sub> / (2n<sub>i</sub>n<sub>j</sub>)<br/>"
                     "MQ = (1/k) Σ<sub>i</sub> cohesion<sub>i</sub> − (1 / choose(k,2)) Σ<sub>i&lt;j</sub> coupling<sub>ij</sub>")
        self.paragraph("The denominator n(n−1) counts the possible directed edges within a cluster when self-loops "
                       "are excluded. The lecture permits alternative density denominators; this report uses the "
                       "one in its worked directed-graph example. A singleton has cohesion zero. A partition with "
                       "one cluster has coupling zero, and an empty partition reports zero by convention. Pairs "
                       "of clusters with no connecting edges still count in the coupling average. Stating these "
                       "choices is necessary to reproduce the same MQ value from the same grouping. [L67 p.17; D9]")
        self.sub("Checking the formula on a small graph")
        self.paragraph("Take clusters C1={a,b} and C2={c,d}, with edges a→b, b→a, c→d, d→c and b→c. "
                       "Each cluster has cohesion 2/(2×1)=1. Their coupling is 1/(2×2×2)=1/8, giving "
                       "<b>MQ=1−1/8=0.875</b>. If an isolated singleton is added as a third cluster, average "
                       "cohesion becomes 2/3 and average coupling becomes (1/8)/3=1/24. MQ is then 5/8. "
                       "None of the original five edges has changed; the lower score follows from averaging "
                       "over the additional cluster and cluster pairs. [D9]")
        self.sub("Interpreting a score")
        self.paragraph("For this graph model, MQ lies between −1 and 1. It describes how dependencies are "
                       "concentrated within groups, but it cannot establish functional correctness, runtime "
                       "performance, developer productivity or user-perceived quality. The averages also give "
                       "a small cluster the same weight as a large one. Cluster count, cluster sizes and the "
                       "treatment of isolates can therefore affect the result. The report includes cohesion "
                       "weighted by class count, edge fractions and cluster-size distributions to help interpret "
                       "the main score. [L67 p.16; L12 p.45; D9]")
        self.paragraph("A1 and A3 are evaluated on the full graph, while A2 and A4 use the graph left after UE "
                       "removal. Comparing a full-graph score directly with a filtered score changes both the "
                       "groups and the classes being assessed. A further comparison addresses this by removing "
                       "the same classes from the full partition and scoring both partitions on exactly the "
                       "retained nodes and edges. MoJoFM and the supplementary Adjusted Rand measure compare "
                       "the memberships of partitions; neither partition is assumed to be ground truth. "
                       "[D3; D9; D16]", "small")


    def growth(self):
        d = self.d
        self.heading("9  Classes and dependencies over time")
        self.paragraph(f"The first selected release has {count(integer(d.first, 'classes'))} classes and "
                       f"{count(integer(d.first, 'dependencies'))} dependencies. By the last release, these "
                       f"counts reach {count(integer(d.last, 'classes'))} and "
                       f"{count(integer(d.last, 'dependencies'))}. The next figure shows the changes across all 30 samples. [D1]")
        self.chart("01_classes_dependencies", caption="Figure 1. Project class counts and distinct directed "
                   "dependencies for 30 major/minor release families. Dependencies come from the instructor's "
                   "extractor. Source: results/sizes.csv.")
        self.paragraph("Classes include project-owned annotation types and isolates, meaning classes with no "
                       "recorded edges. Dependencies exclude annotation applications, following the instructor's "
                       "extractor. This distinction matters when releases change compatibility or nullness "
                       "annotations without comparable changes to executable dependencies. [D1; D6]")
        self.paragraph("The samples are equally spaced along the axis, but the time between releases varies. "
                       "The selection reduces repeated patch observations rather than sampling at regular calendar "
                       "intervals. New functionality, implementation changes, compiler output and static-analysis "
                       "coverage can all affect the counts. Growth alone cannot distinguish these explanations "
                       "or show that design quality has worsened. [L12 pp.43–48; D4]")
        transitions = sorted(d.evolution, key=lambda r: abs(integer(d.by_version[r["version"]], "dependencies") -
                             integer(d.by_version[r["previous_version"]], "dependencies")), reverse=True)[:2]
        self.sub("Largest changes in dependency count")
        for transition in transitions:
            before = d.by_version[transition["previous_version"]]
            after = d.by_version[transition["version"]]
            self.paragraph(f"Between {esc(transition['previous_version'])} and {esc(transition['version'])}, "
                           f"dependencies change from {count(integer(before, 'dependencies'))} to "
                           f"{count(integer(after, 'dependencies'))}. The change-point files list the added and "
                           "removed classes and edges so that this interval can be checked against the source. [D15]", "small")


    def metadata_breakdown(self):
        d = self.d
        self.heading("Annotation types and isolated classes")
        self.paragraph("A class can belong to Guava even when the extractor records no relation to or from it. "
                       "The inventory retains these isolated nodes, including annotation declarations. The next figure "
                       "and the endpoint table show how much of the inventory they represent. [D6]")
        self.chart("09_metadata_isolates", caption="Figure 9. Project-owned annotation types and isolated nodes. "
                   "Annotation declarations remain in the inventory; annotation applications are not edges. "
                   "Source: classes.csv and dependencies.csv for each release.")
        first, last = d.class_breakdown[0], d.class_breakdown[-1]
        self.table(["Inventory category", d.names[0], d.latest], [
            ["All merged project-owned types", count(first["classes"]), count(last["classes"])],
            ["Nonannotation types", count(first["non_annotations"]), count(last["non_annotations"])],
            ["Annotation types", count(first["annotations"]), count(last["annotations"])],
            ["All isolated nodes", count(first["isolates"]), count(last["isolates"])],
            ["Isolated annotation types", count(first["annotation_isolates"]), count(last["annotation_isolates"])],
        ], [WIDTH - 160, 80, 80], small=True, numeric=(1, 2), padding=4)
        self.paragraph("Isolates affect clustering even though they contribute no edges. The ACDC adapter puts "
                       "each isolate in a single-class cluster, whose cohesion is zero under the chosen metric. "
                       "For k-means, an isolate still receives the identity component of its feature row. "
                       "Annotation types can therefore influence class counts, cluster counts and MQ without "
                       "introducing annotation-application edges. [D6; D9]")
        self.paragraph("The categories overlap: an isolated annotation type is included in both the annotation "
                       "and isolate totals. The rows should not all be added together. Lack of member-use evidence "
                       "also does not justify removal by Usage Equality; the detector retains that case. [D2]", "small")


    def release_table(self):
        d = self.d
        self.heading("10  Results for all thirty releases")
        self.paragraph("This table contains the counts behind the growth and filtering figures. Classes are "
                       "project-owned types after merging inner and anonymous classes; edges are distinct directed "
                       "dependencies. The filtering columns show the number of removed classes and the dependencies "
                       "remaining afterwards. [D1; D4]")
        rows = []
        for version, size in zip(d.versions, d.sizes):
            rows.append([version["version"], version["release_date"][:10], count(integer(size, "classes")),
                         count(integer(size, "dependencies")), count(integer(size, "omnipresent_classes")),
                         count(integer(size, "retained_dependencies")),
                         str(len(version["skipped_stable_since_previous"])) if version["index"] > 1 else "—"])
        self.table(["Release", "Published", "Classes", "Edges", "UE out", "Edges left", "Skipped"], rows,
                   [62, 77, 64, 74, 53, 80, WIDTH - 410], small=True, numeric=(2, 3, 4, 5, 6), padding=3.5)
        self.paragraph("“UE out” counts removed classes. “Skipped” counts numeric stable tags strictly between "
                       "this sample and the previous one, including any mainline or backport release excluded "
                       "by the selection rules. The exact tags, Git commit identifiers and artifact variants "
                       "are recorded in config/versions.json. [D4]", "small")


    def removals(self):
        d = self.d
        self.heading("11  Classes removed by Usage Equality")
        self.paragraph("Removing one broadly used class can remove many edges. The next figure compares the number "
                       "of selected classes with the share of dependencies connected to them. The thresholds "
                       "are fixed across releases, and all selected classes are removed in one pass. [D1; D2]")
        self.chart("02_ue_removals", caption="Figure 2. Classes selected by Usage Equality and the fraction of "
                   "full-graph dependencies removed with them. Source: results/sizes.csv.")
        top = d.removal_frequency.most_common(4)
        if top:
            self.table(["Most frequently removed classes", "Releases selected / 30"],
                       [[esc(short_class(name)), str(n)] for name, n in top], [WIDTH - 126, 126], small=True, numeric=(1,), padding=3.5)
        self.paragraph(f"In the latest release, Usage Equality removes {integer(d.last, 'omnipresent_classes')} "
                       f"of {integer(d.last, 'classes')} classes, leaving "
                       f"{count(integer(d.last, 'retained_dependencies'))} dependencies, or "
                       f"{percent(number(d.last, 'edge_retention_fraction'))} of the full graph. Selection does "
                       "not imply poor design: a shared utility can serve its purpose well while making subsystem "
                       "boundaries harder for a clustering algorithm to distinguish. [UE; D1; D2]")
        self.paragraph("The frequency table uses all 30 releases as its denominator, including releases before "
                       "a class first appears. The per-release ue.json and omnipresent.csv files distinguish "
                       "absent classes, retained candidates and selected classes. [D2]", "small")
        self.sub("Two class-level checks")
        self.paragraph("The following cases show why many callers are not enough to trigger removal. The "
                       "columns e and c are the Usage Equality and cardinality scores defined in the method "
                       "section; both must meet their thresholds. [D14]")
        case_rows = []
        for case in d.ue_cases["cases"]:
            score = case["production_score"]
            case_rows.append([esc(short_class(case["class_name"])), str(score["fanin"]), str(score["referenced_members"]),
                              fmt(score["usage_equality"], 4), fmt(score["cardinality"], 4),
                              "Remove" if score["omnipresent"] else "Retain"])
        self.table(["Latest audited class", "Callers", "Members", "e", "c", "Decision"], case_rows,
                   [170, 57, 57, 66, 66, WIDTH - 416], small=True, numeric=(1, 2, 3, 4), padding=3.5)
        self.paragraph("Preconditions meets both thresholds. Iterators has many callers, but Iterables "
                       "dedicates a comparatively large share of its member references to it. The resulting "
                       "maximum dedication of about 0.502 prevents removal. The independent audit records "
                       "the exact fractions, every caller's scores and the supporting member-CSV rows. [D14]")


    def mq_results(self):
        d = self.d
        self.heading("12  Modularization quality")
        self.paragraph("The next figure shows MQ for the four conditions, with each series summarized below it. "
                       "A1 and A3 use the full graph; A2 and A4 use the filtered graph. The algorithms can "
                       "therefore be compared on matching graphs. Comparing before and after filtering "
                       "requires the additional check described later. [D1; D3]")
        self.chart("03_mq", caption="Figure 3. MQ for the four conditions. A1/A3 use full graphs and A2/A4 "
                   "use filtered graphs. A gap between full and filtered scores includes a change in the evaluated graph.")
        rows = []
        for c in CONDITIONS:
            vals = [number(r, "mq") for r in d.series[c]]
            rows.append([CONDITION_LABELS[c], fmt(min(vals)), fmt(statistics.median(vals)), fmt(max(vals)), fmt(vals[-1])])
        self.table(["Condition", "Minimum", "Median", "Maximum", "Latest"], rows,
                   [185, 77, 77, 77, WIDTH - 416], numeric=(1, 2, 3, 4))
        full_wins = sum(d.metric("A1", "mq", v) > d.metric("A3", "mq", v) + 1e-12 for v in d.names)
        filtered_wins = sum(d.metric("A2", "mq", v) > d.metric("A4", "mq", v) + 1e-12 for v in d.names)
        self.paragraph(f"ACDC scores higher than k-means in {full_wins} of the 30 full-graph comparisons "
                       f"and {filtered_wins} of the filtered-graph comparisons. The difference depends on "
                       "the metric and on how finely each algorithm divides the classes. It does not establish "
                       "agreement with a developer-approved architecture. Cluster sizes are examined below "
                       "to help interpret the scores. [D1; D9]")


    def components(self):
        self.heading("13  Cohesion and coupling")
        self.paragraph("MQ subtracts average coupling from average cohesion. Showing both terms helps "
                       "explain whether a change comes from denser internal groups or different relationships "
                       "between groups. The next figure uses a separate vertical scale for each term. [D9]")
        self.chart("04_cohesion_coupling", caption="Figure 4. Average cohesion and coupling. Cohesion averages "
                   "over clusters; coupling averages over unordered cluster pairs. The vertical scales differ.")
        self.paragraph("These are averages over clusters and cluster pairs, not individual classes or edges. "
                       "Cluster sizes and the number of pairs therefore affect the result. In particular, "
                       "low average coupling need not mean that few dependencies cross cluster boundaries. [D9]")
        self.paragraph("An appendix result can be reconstructed from its A&lt;n&gt;_quality/per_cluster.csv "
                       "and per_pair.csv files: sum the normalized terms, divide by the respective numbers "
                       "of clusters and unordered pairs, then subtract coupling from cohesion. Values in "
                       "the report are rounded; the CSV and JSON files retain the calculation precision. [D9]", "small")


    def same_graph_results(self):
        d = self.d
        self.heading("14  The effect of filtering on the grouping")
        self.paragraph("To separate regrouping from a change in the measured graph, the original partition "
                       "is first restricted to the retained classes. This removes selected classes without "
                       "regrouping the survivors; empty clusters disappear. That partition and the newly "
                       "clustered filtered partition are then scored on exactly the same retained edges. [D3]")
        self.chart("05_same_graph", caption="Figure 5. MQ difference between clustering the filtered graph "
                   "again and keeping the original grouping of retained classes. Positive values favour "
                   "reclustering. ARI records partition agreement. Source: results/same_graph_comparisons.csv.")
        rows = []
        for full, name in (("A1", "ACDC"), ("A3", "k-means")):
            comp = d.comparison(full)
            vals = [number(r, "mq_change_same_graph") for r in comp]
            rows.append([name, fmt(statistics.median(vals), 4), fmt(vals[-1], 4),
                         fmt(number(comp[-1], "adjusted_rand_agreement")),
                         str(sum(v > 1e-12 for v in vals)), str(sum(v < -1e-12 for v in vals))])
        self.table(["Algorithm", "Median ΔMQ", "Latest ΔMQ", "Latest ARI", "Δ > 0", "Δ < 0"], rows,
                   [85, 95, 93, 83, 68, WIDTH - 424], small=True, numeric=(1, 2, 3, 4, 5))
        self.paragraph("Here, ΔMQ is the score after reclustering minus the score for the original grouping "
                       "of retained classes. Holding the graph fixed makes this a comparison of the groupings "
                       "produced by the stated recovery procedure. It does not establish that filtering helps "
                       "every algorithm or software system. [D3]")


    def agreement_results(self):
        d = self.d
        self.heading("Agreement between partitions: MoJoFM")
        self.paragraph("MQ describes a partition's structure; MoJoFM measures how similar two partitions "
                       "are. Before comparing a full-graph result with a filtered result, both are restricted "
                       "to the same retained classes. The next figure shows the lecture's agreement measure over "
                       "the sampled history. [L67; D16]")
        self.chart("11_mojofm", caption="Figure 11. MoJoFM agreement on the retained class set, on a 0–100 "
                   "scale. Forward and reverse comparisons use different reference partitions. [D16]")
        rows = [r for r in d.partition_comparisons if r["version"] == d.latest and r["scope"] != "temporal_full_common"]
        self.table(["Latest comparison", "Nodes", "Forward", "Reverse", "ARI"], [
            [esc(r["source_condition"] + " → " + r["reference_condition"]), count(integer(r, "n_nodes")),
             fmt(number(r, "mojofm"), 2), fmt(number(r, "reverse_mojofm"), 2), fmt(number(r, "adjusted_rand_agreement"), 4)]
            for r in rows], [150, 65, 93, 93, WIDTH - 401], small=True, numeric=(1, 2, 3, 4))
        self.formula("MoJoFM(P → Q) = 100 × [1 − MoJo(P,Q) / maxMoJo(Q)]")
        self.paragraph("MoJo counts the fewest object moves and cluster joins needed to transform partition "
                       "P into reference partition Q. The normalizer depends on Q, so reversing the comparison "
                       "can change MoJoFM. Saved results include both directions, distances, denominators, "
                       "cluster counts and a hash of the exact class set. Normalized scores for empty or "
                       "one-class sets are recorded as undefined. [L67; D16]")
        self.paragraph("An expert reference is needed to interpret this score as recovery accuracy, but not "
                       "to measure agreement between two stated partitions. This corrects the earlier reason "
                       "for omitting MoJoFM. The Adjusted Rand Index (ARI) remains a supplementary measure whose "
                       "value is unchanged when the inputs are reversed. Neither measure assesses module names "
                       "or responsibilities. Temporal and AI comparisons use the same common-class rule. [D16]")


    def granularity(self):
        d = self.d
        self.heading("15  Cluster sizes and the interpretation of MQ")
        self.paragraph("MQ differences can partly reflect one algorithm producing many small clusters and "
                       "another producing fewer large ones. The next figure shows the number of clusters and the "
                       "fraction of classes in the largest one. The table adds details for the latest release. [D9]")
        self.chart("06_granularity", caption="Figure 6. Number of clusters and fraction of classes in the "
                   "largest cluster. ACDC's subgraph-size parameter does not cap the final cluster size.")
        rows = []
        for c in CONDITIONS:
            r = d.by_metric[d.latest, c]
            rows.append([c, count(integer(r, "n_clusters")), count(integer(r, "max_cluster_size")),
                         count(integer(r, "singleton_clusters")), fmt(number(r, "size_weighted_cohesion")),
                         percent(number(r, "inter_edge_fraction"))])
        self.table(["Latest", "k", "Largest", "Singletons", "Size-weighted cohesion", "Inter-edge share"], rows,
                   [51, 43, 65, 74, 142, WIDTH - 375], small=True, numeric=(1, 2, 3, 4, 5))
        self.paragraph("Size-weighted cohesion gives larger clusters more influence in proportion to their "
                       "class counts. The lecture's MQ instead weights each nonempty cluster equally. Inter-edge "
                       "share is the fraction of all dependencies crossing cluster boundaries. These additional "
                       "measures help reveal large residual groups or numerous small clusters that averages can "
                       "obscure; they do not replace the required MQ calculation. [D9]")


    def temporal(self):
        d = self.d
        self.heading("16  Changes between sampled releases")
        self.paragraph("Total counts can hide replacement: one release may add classes while removing "
                       "others. The next figure separates additions and removals and compares the dependencies and "
                       "partitions of classes present in both adjacent samples. [D10; D16]")
        self.chart("07_temporal_change", caption="Figure 7. Class-name changes and structural agreement "
                   "between adjacent samples. Agreement uses shared class names. Sample intervals vary in length.")
        churn = max(d.evolution, key=lambda r: integer(r, "added_classes") + integer(r, "removed_classes"))
        self.paragraph(f"The largest turnover is between {esc(churn['previous_version'])} and "
                       f"{esc(churn['version'])}, with {integer(churn, 'added_classes')} class names added "
                       f"and {integer(churn, 'removed_classes')} removed. Matching by name counts renames and "
                       "package moves as well as additions and deletions. Compiler output or changes in what "
                       "the model observes can also affect the inventory. These counts therefore do not directly "
                       "measure features gained or lost. [D10]")
        self.paragraph("The public-suffix implementation illustrates this distinction. It remains within "
                       "the project boundary when it moves from com.google.common.net to "
                       "com.google.thirdparty.publicsuffix, although a renamed class can still count as one "
                       "removal and one addition. [D4; D6]")
        self.paragraph("Edge Jaccard compares dependencies among shared classes. It can remain high while "
                       "new or removed classes cause large changes in total edges. Temporal MoJoFM and ARI "
                       "compare A1/A3 partitions restricted to those same shared classes. These measures "
                       "describe stability between samples, rather than correctness against an intended architecture. [D10; D16]")


    def change_evidence(self):
        d = self.d
        self.heading("Relating graph changes to the source")
        self.paragraph("Four intervals illustrate how changes in the graph relate to identifiable source "
                       "changes. The audit stores added and removed classes, exact edge differences and hashes "
                       "of source-JAR entries so these observations can be checked against the artifacts. [D15]")
        points = {(p["before_version"], p["after_version"]): p for p in d.changes["change_points"]}
        selected = [("13.0.1", "15.0"), ("19.0", "21.0"), ("33.2.1", "33.4.8"), ("33.4.8", "33.5.0")]
        self.table(["Sample transition", "Classes", "Edges", "Edge change"], [
            [esc(a + " → " + b), f"{points[a,b]['counts']['classes_before']} → {points[a,b]['counts']['classes_after']}",
             f"{points[a,b]['counts']['edges_before']} → {points[a,b]['counts']['edges_after']}",
             fmt(points[a,b]["counts"]["edge_change_percent"], 2) + "%"] for a, b in selected
        ], [143, 107, 130, WIDTH - 380], small=True, padding=4)
        point = points["13.0.1", "15.0"]
        self.sub("13.0.1 to 15.0: collections, escaping and I/O")
        self.paragraph(f"This interval adds {point['counts']['added_classes']} class names and removes "
                       f"{point['counts']['removed_classes']}. Additions include "
                       f"{point['added_classes_by_package']['com.google.common.collect']} collection types, "
                       f"{point['added_classes_by_package']['com.google.common.escape']} escaping types and "
                       f"{point['added_classes_by_package']['com.google.common.io']} I/O types. "
                       "ImmutableRangeMap and ImmutableRangeSet are examples. This establishes growth in the "
                       "implementation inventory, although each new class need not be a separate user-facing feature. [D15]")
        point = points["19.0", "21.0"]
        self.sub("19.0 to 21.0: the graph package")
        self.paragraph(f"Of {point['counts']['added_classes']} added class names, "
                       f"{point['added_classes_by_package']['com.google.common.graph']} belong to "
                       "com.google.common.graph. Edge Jaccard among shared classes is "
                       f"{fmt(point['counts']['common_node_edge_jaccard'], 4)}, showing that many existing "
                       "relationships remain stable as new types account for much of the growth. There is an "
                       "unsampled release in this interval, so the comparison does not locate the first "
                       "introduction commit. [D15]")
        point = points["33.2.1", "33.4.8"]
        self.sub("33.2.1 to 33.4.8: nullness annotations")
        self.paragraph("The earlier source declares ElementTypesAreNonnullByDefault internally and uses "
                       "it in Lists.java. The later source contains package-level @NullMarked and a JSpecify "
                       f"import. Across the interval, {point['counts']['removed_annotation_classes']} annotation "
                       f"types disappear and {point['counts']['added_annotation_classes']} appear, while edges "
                       f"change by only {fmt(point['counts']['edge_change_percent'], 2)}%. Excluding annotation "
                       "applications from the instructor's graph avoids the large metadata-driven edge "
                       "fluctuations seen in the earlier report. Annotation declarations still contribute "
                       "to class and isolate counts. [D15]")
        point = points["33.4.8", "33.5.0"]
        self.sub("33.4.8 to 33.5.0: collection support classes")
        self.paragraph(f"All {point['counts']['removed_classes']} removed class names belong to collections: "
                       "seven nonannotation types and GwtTransient. They include GWT serialization dependency "
                       "helpers, ForwardingImmutableCollection and ImmutableEntry. The graph loses "
                       f"{point['counts']['removed_edges']} edges and gains {point['counts']['added_edges']}. "
                       "These are identifiable implementation changes, without being sufficient evidence of "
                       "architectural improvement or loss of public functionality. [D15]")


    def cluster_profiles(self):
        d = self.d
        self.heading("17  Interpreting the largest recovered groups")
        self.paragraph("A cluster's members help explain what the algorithm has grouped together. The tables "
                       "below show the five largest clusters from ACDC and k-means on the latest full graph, "
                       "along with their most common packages and example classes. Package names are added "
                       "after clustering to aid interpretation; they were not algorithm features. [D7]")
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
                rows.append([esc(cluster), str(len(names)), esc(composition) + "<br/>" + esc(examples)])
            self.table(["Cluster", "Classes", "Main packages; example classes"], rows,
                       [76, 43, WIDTH - 119], small=True, numeric=(1,), padding=4.5)
        self.paragraph("Cluster identifiers are output labels, not established subsystem names. ACDC's saved "
                       "original_containers map links these labels to the implementation's container names, "
                       "including any orphan container. This matters when interpreting a large group that "
                       "may contain classes left over from the main recovery steps. Complete assignments are "
                       "available for every condition and release. [D7]")


    def ai_sections(self):
        """Read the saved AI experiment and present its inputs and results."""
        d = self.d
        self.heading("18  An AI interpretation of Guava 33.7.2")
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
        self.paragraph(f"The final experiment asks an AI model to propose a decomposition of Guava "
                       f"{esc(record['version'])}, the latest release in the study. The model was "
                       f"{esc(record['model'])}. It first outlined a possible architecture using class names and "
                       "package counts. It then examined the dependency graph and package documentation before "
                       "assigning every class to a module. This produced one final architecture; the earlier outline "
                       "was retained to show how its reasoning changed. [AS pp.3–4; D12]")
        self.sub("What the model received")
        self.paragraph(f"The graph supplied to the model contains {count(metrics['n_nodes'])} classes and "
                       f"{count(metrics['n_edges'])} directed dependencies. The package documentation comes from "
                       "the source JAR for the same release. The files below record these inputs; the checksum "
                       "prefixes identify the exact copies used. [D12]")
        self.table(["Input file", "Bytes", "SHA-256 prefix"], [
            [esc(Path(item["path"]).name), count(item["bytes"]), item["sha256"][:16]] for item in record["input_files"]
        ], [235, 70, WIDTH - 305], small=True, numeric=(1,))
        self.paragraph("The model was given no ACDC or k-means partitions, usage-equality decisions or metric "
                       "results. It could not browse external sources. Its final assignment had to place each class "
                       "in exactly one module before the evaluation script calculated quality. The saved experiment "
                       "record contains the full checksums, file paths, activity log and outputs. [D12]")
        self.sub("How to interpret this comparison")
        self.paragraph("The experiment record sets out three limits on the comparison and its reproducibility:")
        for note in record["notes"]:
            self.paragraph(esc(note))
        self.paragraph("The initial outline is saved in initial_hypothesis.md and the final explanation in "
                       "response.md. The sections that follow give the prompt, the proposed modules and their "
                       "evaluation. The scores can be recalculated from the saved assignment. Asking the model "
                       "again may produce a different architecture. [D12]", "small")
        if additional_prompts:
            self.sub("Additional instructions given to the model")
            self.paragraph("The additional recorded instruction appears below, unchanged. It contained no baseline "
                           "partition or quality score. No completion or status follow-up was saved for this revised "
                           "experiment. The main task prompt follows in the next section. [D12]", "tiny")
            for item in additional_prompts:
                path = ROOT / item["path"]
                label = "Launch instruction" if path.name == "launch_message.txt" else "Coordinator follow-up"
                self.paragraph(f"<b>{label}:</b> " + esc(path.read_text().strip()), "tiny")
                self.paragraph(f"SHA-256: {item['sha256']}", "tiny")

        self.heading("19  The experiment prompt")
        self.paragraph("This is the saved prompt, reproduced verbatim so that the task given to the model can be "
                       "checked. The record does not include hidden platform instructions or model internals. [D12]", "small")
        for block in prompt_path.read_text(encoding="utf-8").strip().split("\n\n"):
            self.paragraph(esc(block).replace("\n", "<br/>"), "small")
        self.paragraph("Prompt SHA-256: " + esc(record["prompt_sha256"]), "mono")

        self.heading("20  The proposed modules")
        self.paragraph(f"The model grouped all {count(len(ai_classes))} classes into {len(module_counts)} modules, "
                       "with each class assigned exactly once. The table summarises the responsibilities it "
                       "gave those modules. These descriptions express the model's reading of the names, "
                       "documentation and dependencies; they have not been endorsed by Guava's maintainers. "
                       "The full architecture file explains each proposed boundary and the observations behind it. [D12]")
        self.table(["Module", "Classes", "Responsibility excerpt"], [
            [esc(m["name"]), count(m["class_count"]), esc(excerpt(m["responsibility"], 155))] for m in architecture["modules"]
        ], [150, 48, WIDTH - 198], small=True, numeric=(1,), padding=3.2)
        self.paragraph("Every class assignment is listed in results/ai/assignment.csv. The explanation and initial "
                       "outline are in response.md and initial_hypothesis.md in the same directory. The module "
                       "definitions, revisions and limitations are also recorded in architecture.json. [D12]", "small")

        self.heading("21  Comparing the AI proposal with ACDC and k-means")
        self.paragraph("The AI proposal was evaluated with the same cohesion, coupling and MQ calculations as "
                       "the other partitions. Its complete assignment uses the full graph, allowing comparison "
                       "with A1 and A3. For comparison with A2 and A4, the removed classes were deleted from the "
                       "same assignment and the scores were recalculated on the retained graph. The model was "
                       "not asked to produce another architecture. [D12]")
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
        self.paragraph("Scores should be compared within the same graph: the full-graph rows form one comparison "
                       "and the retained-graph rows form another. MoJoFM and ARI then show how closely the class "
                       "groupings agree. The two MoJoFM columns report each direction separately. [D12]")
        self.table(["Baseline", "Graph", "AI → baseline MoJoFM", "Baseline → AI MoJoFM", "ARI"], [
            [r["condition"], esc(r["graph"]), fmt(number(r, "mojofm_ai_to_baseline"), 2),
             fmt(number(r, "mojofm_baseline_to_ai"), 2), fmt(number(r, "adjusted_rand_agreement"), 4)] for r in comparisons
        ], [58, 71, 137, 137, WIDTH - 403], small=True, numeric=(2, 3, 4), padding=3.5)
        self.sub("How the proposal changed after inspecting the evidence")
        self.paragraph("The following three examples are taken from the model's saved explanation. They show "
                       "how the graph and documentation affected its initial outline. [D12]", "small")
        changes = architecture.get("changes_from_initial_hypothesis", [])
        if isinstance(changes, str):
            changes = [changes]
        for change in changes[:3]:
            if isinstance(change, dict):
                change = " ".join(str(change[k]) for k in ("final_decision", "evidence_and_reason") if k in change)
            self.paragraph(esc(change), "small")
        self.sub("What the comparison shows")
        ai_vs_kmeans = next(r for r in comparisons if r["condition"] == "A3")
        self.paragraph(f"The AI proposal has MQ {fmt(metrics['mq'], 4)} on the full graph and "
                       f"{fmt(retained['mq'], 4)} on the retained graph. It uses {metrics['n_clusters']} modules, "
                       f"compared with {integer(d.by_metric[d.latest, 'A3'], 'n_clusters')} clusters for A3. "
                       f"Their adjusted Rand agreement is {fmt(number(ai_vs_kmeans, 'adjusted_rand_agreement'), 4)}. "
                       "These measurements describe different aspects of the output: MQ summarises the pattern "
                       "of dependencies within and between groups, while agreement measures compare the actual "
                       "class assignments. [D9; D12]")
        self.paragraph("The methods also work at different levels of detail and receive different information. "
                       "The AI can use names and source documentation to propose semantic responsibilities; the "
                       "structural algorithms follow rules defined over the dependency graph. The results therefore "
                       "do not establish which method best recovers Guava's intended design. Nor do the proposed "
                       "modules establish an acyclic decomposition suitable for separate builds. [D9; D12]")
        ai_vs_acdc = next(r for r in comparisons if r["condition"] == "A1")
        self.paragraph(f"The difference between the two MoJoFM directions is substantial here: transforming the "
                       f"AI proposal towards A1 gives {fmt(number(ai_vs_acdc, 'mojofm_ai_to_baseline'), 2)}, "
                       f"while the reverse gives {fmt(number(ai_vs_acdc, 'mojofm_baseline_to_ai'), 2)}. "
                       "Merging several fine groups may require joins, while separating a coarse group may require "
                       "many individual moves. The target partition also determines the normalization. Both "
                       "directions are needed to describe the comparison. [D12; D16]", "small")
        self.paragraph("The calculations are saved in results/ai/comparisons.csv, metrics.json and "
                       "retained_metrics.json. The model's full account of dependencies between modules and its "
                       "own limitations remains in architecture.json and response.md. [D12]", "small")


    def performance(self):
        d = self.d
        self.heading("22  Running time and memory use")
        ue_times = [number(r, "seconds") for r in d.runtimes if r["stage"] == "UE"]
        self.paragraph(f"The usage-equality detector took a median of {fmt(statistics.median(ue_times), 4)} seconds "
                       "per release, including CSV input. The figure compares the study timings with a separate "
                       "benchmark on larger generated graphs. [D11]")
        self.chart("08_performance", caption="Figure 8. Time spent on the study stages and on the separate "
                   "usage-equality benchmark. The two experiments measure different workloads.")
        rows = []
        for stage in ("extraction", "UE", "A1", "A2", "A3", "A4"):
            values = [number(r, "seconds") for r in d.runtimes if r["stage"] == stage]
            rows.append([stage, fmt(statistics.median(values), 4), fmt(max(values), 4), fmt(sum(values), 3)])
        self.table(["Study stage", "Median per release (s)", "Maximum (s)", "Total for 30 releases (s)"], rows,
                   [92, 151, 104, WIDTH - 347], small=True, numeric=(1, 2, 3), padding=3.8)
        self.paragraph("Extraction includes Java startup and file I/O; clustering covers each adapter call. "
                       "Downloads, the pilot, tests and report generation are excluded. The totals therefore "
                       "represent the measured stages, rather than elapsed time for the entire project. [D11]", "small")
        self.sub("Testing larger inputs")
        self.paragraph("Generated graphs have degree 20. Each timed detector call includes validation and "
                       "diagnostics, and every node's expected score is checked. The table gives medians from "
                       "three repeats. [D11]", "small")
        rows = [[count(c["classes"]), count(c["distinct_member_references"]), fmt(c["median_seconds"], 4),
                 fmt(c["process_high_water_rss_mib"], 1)] for c in d.benchmark["cases"]]
        self.table(["Classes", "Member references", "Median time (s)", "Peak process memory (MiB)"], rows,
                   [92, 137, 97, WIDTH - 326], small=True, numeric=(0, 1, 2, 3), padding=3.8)
        self.paragraph("Peak resident memory is cumulative for the process, including generated inputs and "
                       "objects from earlier runs; it is not memory per detector call. Times depend on the "
                       "machine and software. The results cover the tested sizes only: no speedup or correctness "
                       "comparison with the old JNode executable was made. [D11]", "small")


    def discussion(self):
        self.heading("23  Discussion")
        self.sub("What has been reconstructed?")
        self.paragraph("The study reconstructs architecture by grouping classes from a static dependency graph. "
                       "It therefore describes possible higher-level views of Guava's implementation. This "
                       "distinction matters in the architecture-evolution lecture, which separates implemented, "
                       "intended and described architecture, and static and dynamic views. To demonstrate "
                       "architectural erosion, the study would also need an intended design rule and evidence "
                       "that later changes violate it. A fall in MQ alone cannot establish that. [L5 PDF pp.9,12,14,18–19]")
        self.sub("Relating the changes to Lehman's laws")
        self.paragraph("The changes in class and dependency counts are consistent with continuing change, and "
                       "the source examples help explain what changed between releases. They also provide a "
                       "starting point for investigating structural complexity. Applying the wider claims in "
                       "Lehman's laws requires further evidence: functional growth needs information about "
                       "requirements and features; perceived quality needs user evidence; and claims about "
                       "effort or organisational stability need process data. The lectures apply these laws to "
                       "E-type systems. Applying them to Guava therefore also requires an explanation of how "
                       "the library adapts to changing real-world needs. [L12 pp.33–48]")
        self.sub("Why the definitions matter")
        self.paragraph("The requirements lectures emphasise clear, measurable statements and the ability to trace "
                       "a conclusion back to its evidence. That is why the report defines what counts as an "
                       "internal class, a dependency, a stable release, an omnipresent class and a quality score. "
                       "For example, a dependency in a compiled class file is a different observation from a "
                       "relationship between requirements or an interaction observed while the program runs. "
                       "Saving the inputs, parameters and per-cluster calculations makes these choices and their "
                       "consequences checkable. It does not, by itself, make the choices correct. "
                       "[L3 pp.9–19,27–33; L4 pp.11–15]")
        self.sub("Limitations")
        self.paragraph("The 30 releases were selected systematically from the eligible history. They are a "
                       "sparse sample, so changes between the selected releases may be missed. The analysis "
                       "also has a deliberate boundary: it covers the chosen Guava artifact and source "
                       "namespaces, excluding external libraries and other modules. The findings describe "
                       "that boundary rather than every interaction in an application that uses Guava. [D2; D4]")
        self.paragraph("A static graph cannot capture every reflective call or dependency created at runtime. "
                       "Differences in compilers and inlining can also affect published bytecode. The "
                       "usage-equality detector depends on resolving member use and on its chosen thresholds; "
                       "it implements a different method from the older Noise detector. The structure recovered "
                       "by ACDC depends partly on how finely it divides the graph, while k-means depends on "
                       "the feature geometry and the way the pilot's k rule is applied to other releases. "
                       "[D4; D6; D7]")
        coverage = self.d.ue_cases["resolution_coverage"]
        self.paragraph(f"For the latest release, {coverage['unresolved_event_rows']} member-use events could not "
                       "be resolved "
                       f"({coverage['distinct_recorded_references']} distinct recorded references); "
                       f"{coverage['unresolved_interclass_event_rows_after_merging']} of these events cross class "
                       "boundaries after inner and anonymous classes have been merged. The diagnostics identify "
                       "a gap in the member-use evidence. Dividing these counts by all recorded calls would "
                       "mix external and intraclass events, so that ratio would not measure extraction "
                       "completeness or the false-negative rate. [D14]", "small")


    def reproduction(self):
        d = self.d
        self.heading("Running the study again")
        self.paragraph("The repository contains the inputs, code and saved results needed to repeat the analysis. "
                       "First install the Python package versions and Java tools listed in the README. Then use "
                       "the commands below to unpack the saved inputs, check them, rebuild the analysis and create "
                       "the report. The --offline option checks the existing artifact cache; the acquisition guide "
                       "also explains how to download the files again.")
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
        self.sub("Following a result back to its input")
        self.paragraph("For a particular release, start with its row in results/metrics.csv. Its assignment file "
                       "shows which cluster contains each class, and its graph files show the dependencies used "
                       "to calculate the score. The version manifest then leads back to the downloaded release. "
                       "The main files are listed below. [D1; D5; D9]")
        self.table(["Artifact path", "What it contains"], [
            ["config/versions.json", "30 distinct families with immutable representatives, URLs, hashes and catalog decisions."],
            ["data/graphs/&lt;version&gt;/", "Original instructor input/raw output; normalization; typed and binary edges; aliases; separate supplemental member evidence and comparisons."],
            ["results/versions/&lt;version&gt;/", "UE scores, retained graph, exactly one A1–A4 assignment and its execution/quality details."],
            ["results/*.csv", "30 size rows, 120 metric rows, 60 same-graph rows, 29 transitions, 180 stage timings, 178 directional comparison pairs."],
            ["results/run_manifest.json", "Input/config hashes, algorithm-source hashes, Python, Java and package versions."],
            ["results/ai/", "Actual AI prompts, provided input, output, coverage audit and comparison."],
            ["report/report_manifest.json", "Hashes of files read by the report and generated PDF/figures; no recomputed partitions."],
        ], [195, WIDTH - 195], small=True)
        package_line = "; ".join(f"{name} {version}" for name, version in d.run["packages"].items())
        self.paragraph(f"The recorded run used Python {esc(d.run['python'].split()[0])}; {esc(package_line)}. "
                       "The Java version and operating system are also saved in run_manifest.json. Input order and "
                       "random seeds are fixed. A different software environment can still affect floating-point "
                       "details and execution time. [D11]", "small")
        self.paragraph("Selection SHA-256: " + esc(d.run["manifest_sha256"]) + "<br/>"
                       "Configuration SHA-256: " + esc(d.run["config_sha256"]), "mono")
        self.paragraph("The larger input and per-release files are stored in ZIP archives under archives/versions. "
                       "The unpack command restores their paths. Summary tables, source code, figures and guides "
                       "can be read directly in the repository.", "small")
        audit = read_json(ROOT / "results/validation.json")
        if audit["status"] != "passed" or audit["failure_count"]:
            raise ValueError("The final report requires a passed independent result audit")
        self.sub("Adapting Java names for ACDC")
        self.paragraph("ACDC expects file names and removes the final dotted suffix when it forms a basename. "
                       "Passing Java class names directly could therefore collapse distinct classes to the same "
                       "package name. The adapter maps p.A to p.A.java before running ACDC and reverses the mapping "
                       "before evaluation. Every edge is preserved, and node_id_map.csv records the mapping. "
                       "The original ACDC source is unchanged. [D7]")
        self.sub("Checking the calculations independently")
        self.paragraph(f"The independent audit {esc(audit['status'])}: it performed "
                       f"{count(audit['checks_performed'])} checks with {audit['failure_count']} failures. "
                       "A separate implementation, using Python's standard library, recalculates Usage Equality "
                       "with exact fractions, lecture MQ, ARI and directional MoJoFM from the saved files. It checks "
                       "all 120 final partitions, the 14 pilot inertia values and the AI output. These checks show "
                       "that the calculations agree; they cannot establish that static extraction finds every "
                       "dependency or that a recovered grouping matches the intended design. [D13]", "small")

    def metric_appendix(self):
        d = self.d
        for page in range(4):
            start = page * 8
            subset = d.names[start:start + 8]
            if page:
                self.story.append(PageBreak())
            self.heading(f"Releases {subset[0]} to {subset[-1]}")
            self.paragraph(f"Selected releases {start + 1}–{start + len(subset)} of 30. Each row gives the final "
                           "result for one release and condition. The saved files include full precision and the "
                           "individual cluster and cluster-pair terms. [D1; D9]", "small")
            rows = []
            for v in subset:
                for c in CONDITIONS:
                    r = d.by_metric[v, c]
                    rows.append([v, c, str(integer(r, "n_nodes")), str(integer(r, "n_clusters")),
                                 fmt(number(r, "cohesion"), 4), fmt(number(r, "coupling"), 4), fmt(number(r, "mq"), 4),
                                 percent(number(r, "inter_edge_fraction"), 0), str(integer(r, "max_cluster_size"))])
            self.table(["Release", "Run", "N", "k", "Cohesion", "Coupling", "MQ", "Inter %", "Largest"], rows,
                       [55, 34, 40, 34, 73, 73, 70, 58, WIDTH - 437], small=True,
                       numeric=(2, 3, 4, 5, 6, 7, 8), padding=2.5)
            self.paragraph("N: evaluated nodes. k: nonempty clusters. Inter %: percentage of graph edges that cross "
                           "clusters. Largest: maximum cluster size. A1=ACDC/full; A2=ACDC/UE filtered; "
                           "A3=KMeans/full; A4=KMeans/UE filtered. Rounded displayed terms can differ in their "
                           "last digit from subtracting rounded cohesion and coupling.", "tiny")

    def references(self):
        self.chapter("References", label="")
        self.paragraph("Page numbers below refer to PDF pages unless a printed slide number is stated. "
                       "Repository paths are relative to the project root.", "small")
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
            ("UE", "Yano and Matsuo (2020), Moderate Detection and Removal of Omnipresent Modules in Software Clustering, ICSME, pp.662–666. Equations 1–3: p.663; procedure: p.664.", "https://doi.org/10.1109/ICSME46990.2020.00068"),
            ("NOISE", "Constantinou, Kakarontzas and Stamelos (2015), Journal of Systems and Software 107, pp.142–157. The earlier significance-based method.", "https://doi.org/10.1016/j.jss.2015.05.065"),
            ("ACDC", "Original ACDC author archive, preserved and SHA-256 pinned in third_party/acdc.", "https://www.eecs.yorku.ca/~bil/downloads/acdc.tar"),
            ("SK", "scikit-learn 1.8 KMeans API and normalize API; actual installed version is recorded by the run.", "https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html"),
            ("JVMS", "Java Virtual Machine Specification 21, §5.4.3.2–5.4.3.4: field and method resolution.", "https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html"),
            ("G1", "Guava source repository and project overview.", "https://github.com/google/guava"),
            ("G2", "Guava ReleaseHistory, with linked historical release notes.", "https://github.com/google/guava/wiki/ReleaseHistory"),
        ]
        for key, description, url in webrefs:
            self.paragraph(f"<b>[{key}]</b> {esc(description)} "
                           f"<link href='{esc(url)}' color='#111111'>{esc(url)}</link>", "tiny")
        self.story.append(PageBreak())
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
        self.contents()
        self.chapter("Purpose and main findings")
        self.executive()
        self.chapter("The releases and their dependency graphs")
        self.selection()
        self.provenance()
        self.structural_model()
        self.chapter("How the architectures are recovered and evaluated")
        self.ue_method()
        self.recovery_methods()
        self.pilot()
        self.quality()
        self.chapter("How Guava changes over time")
        self.growth()
        self.metadata_breakdown()
        self.temporal()
        self.change_evidence()
        self.chapter("Comparing the recovered architectures")
        self.removals()
        self.mq_results()
        self.components()
        self.same_graph_results()
        self.agreement_results()
        self.granularity()
        self.cluster_profiles()
        self.chapter("The AI-assisted architecture proposal")
        self.ai_sections()
        self.chapter("Discussion and practical limits")
        self.discussion()
        self.performance()
        self.chapter("Reproducing the analysis")
        self.reproduction()
        self.chapter("The 30 selected releases", label="A")
        self.release_table()
        self.chapter("All final quality measurements", label="B")
        self.metric_appendix()
        self.chapter("Changes from the earlier study", label="C")
        self.revision()
        self.references()
        ReportDoc(path, self.figure_placements).multiBuild(self.story)
        if len(self.figure_placements) != 11:
            raise ValueError("Expected all 11 vector figures in the final PDF")
        embed_vector_figures(path, self.figure_placements)


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
                      "render": str(image_path.relative_to(ROOT)), "out_of_page_text_blocks": outside,
                      "non_grayscale_text_spans": sum(
                          len({(span["color"] >> shift) & 255 for shift in (0, 8, 16)}) > 1
                          for block in blocks if block.get("type") == 0
                          for line in block["lines"] for span in line["spans"]
                      )})
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
        "packages": {name: importlib.metadata.version(name) for name in ("reportlab", "matplotlib", "numpy", "PyMuPDF")},
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(set(data.inputs) | READ_INPUTS)},
        "method_sources": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(
            list((ROOT / "src/evolution").glob("*.py")) + list((ROOT / "docs").glob("*.md"))
            + [ROOT / "java/DependencyExtractor.java", ROOT / "scripts/fetch_data.py"]
        )},
        "figures": {str(p.relative_to(ROOT)): sha256(p) for p in figures},
        "sections": builder.sections,
        "study_revision": 2, "architecture_count": 120, "metric_appendix_rows": 120,
        "presentation": {
            "style": "Plain academic typography; black and gray throughout",
            "navigation": "Linked contents and numbered sections; complete data tables in appendices",
            "prose": "Revised explanations, introductions and transitions; scientific results unchanged",
            "figures": "Vector PDF charts for sharp printing and smaller file size",
        },
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
