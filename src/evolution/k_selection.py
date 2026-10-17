"""One-pilot inertia elbow; no final-MQ information enters the selection."""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def select_elbow(points: Iterable[Mapping], *, minimum_gap: float = 0.02,
                 fallback_k: int = 30) -> dict:
    """Find the largest positive gap below the normalized endpoint chord.

    With x=(k-k_min)/(k_max-k_min) and y=(I-I_last)/(I_first-I_last),
    gap=1-x-y. Smaller k wins exact ties. A predeclared nearest-candidate
    fallback handles flat/nondecreasing/no-clear-elbow curves. The full raw
    curve and any nonmonotonicity are retained; no smoothing changes evidence.
    """
    curve = sorted([{"k": int(p["k"]), "inertia": float(p["inertia"])} for p in points], key=lambda p: p["k"])
    if not curve or len({p["k"] for p in curve}) != len(curve):
        raise ValueError("Need a nonempty curve with unique candidate k values")
    if any(p["k"] < 1 or not math.isfinite(p["inertia"]) or p["inertia"] < 0 for p in curve):
        raise ValueError("Candidate k/inertia is invalid")
    if not math.isfinite(minimum_gap) or minimum_gap < 0 or fallback_k < 1:
        raise ValueError("Invalid elbow policy")
    k_span = curve[-1]["k"] - curve[0]["k"]
    i_span = curve[0]["inertia"] - curve[-1]["inertia"]
    for point in curve:
        point["normalized_k"] = (point["k"] - curve[0]["k"]) / k_span if k_span else 0.0
        point["normalized_inertia"] = (point["inertia"] - curve[-1]["inertia"]) / i_span if i_span > 0 else None
        point["chord_gap"] = (1.0 - point["normalized_k"] - point["normalized_inertia"]) if k_span and i_span > 0 else 0.0
    interior = curve[1:-1]
    best = max(interior, key=lambda p: (p["chord_gap"], -p["k"])) if interior else None
    clear = bool(best and best["chord_gap"] >= minimum_gap and i_span > 0)
    selected = best if clear else min(curve, key=lambda p: (abs(p["k"] - fallback_k), p["k"]))
    return {
        "selected_k": selected["k"], "clear_elbow": clear,
        "reason": "maximum_normalized_chord_gap" if clear else "predeclared_fallback_no_clear_elbow",
        "maximum_interior_gap": best["chord_gap"] if best else 0.0,
        "minimum_gap": minimum_gap, "fallback_requested_k": fallback_k,
        "nonmonotone_steps": sum(b["inertia"] > a["inertia"] for a, b in zip(curve, curve[1:])),
        "curve": curve,
        "interpretation": "Pilot inertia geometry only; not an optimal or true architectural cluster count; no MQ used in selection",
    }
