"""JNode-UE: member-aware omnipresent detection from Yano and Matsuo (2020).

This is the usage-equality (UE) method in equations 1--3, printed page 663,
of ``Moderate Detection and Removal of Omnipresent Modules in Software
Clustering``.  It is a replacement for, not an implementation of, the earlier
ComponentRank/shortest-path JNode algorithm compared with UE in that paper.

The input owners must already be canonical, outermost project classes.  Member
identifiers must retain their original declaring class, kind, and descriptor:
merging class owners must not merge distinct methods with the same signature.
Only distinct method/field member dependencies supply evidence for UE.  Other
class relations (such as inheritance) do not become fabricated member edges.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from fractions import Fraction
from math import fsum, isfinite, ulp
from typing import TypeAlias


MemberEdge: TypeAlias = tuple[str, str] | Mapping[str, str]


@dataclass(frozen=True, slots=True)
class UEClassScore:
    """The complete decision for one normalized project class."""

    class_name: str
    fanin: int
    referenced_members: int
    max_dedication: float | None
    usage_equality: float | None
    cardinality: float | None
    strongest_caller: str | None
    usage_equality_passed: bool
    cardinality_passed: bool
    omnipresent: bool
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class UEDedication:
    """Equation 1 for a distinct pair of owner classes."""

    source_class: str
    target_class: str
    referenced_members: int
    dedication: float


@dataclass(frozen=True, slots=True)
class UEStats:
    """Counts reconciling input rows with the scoped, deduplicated evidence."""

    classes: int
    input_member_edges: int
    excluded_external_edges: int
    excluded_intraclass_edges: int
    duplicate_member_edges: int
    unique_member_edges: int
    referenced_target_members: int
    class_pairs: int


@dataclass(frozen=True, slots=True)
class UEResult:
    usage_threshold: float
    cardinality_threshold: float
    scores: tuple[UEClassScore, ...]
    dedications: tuple[UEDedication, ...]
    stats: UEStats

    @property
    def removed_classes(self) -> tuple[str, ...]:
        return tuple(score.class_name for score in self.scores if score.omnipresent)

    @property
    def retained_classes(self) -> tuple[str, ...]:
        return tuple(score.class_name for score in self.scores if not score.omnipresent)

    def by_class(self) -> dict[str, UEClassScore]:
        return {score.class_name: score for score in self.scores}

    def to_dict(self, *, include_dedications: bool = False) -> dict:
        """Return JSON-safe, deterministically ordered evidence.

        Per-class decisions always appear.  The optional pair table is useful
        when explaining an individual decision but can make release JSON large.
        """
        result = {
            "algorithm": "JNode-UE (Yano and Matsuo, 2020)",
            "scope": "resolved project member-use graph; normalized outermost owners",
            "usage_threshold": self.usage_threshold,
            "cardinality_threshold": self.cardinality_threshold,
            "removed_classes": list(self.removed_classes),
            "scores": [score.to_dict() for score in self.scores],
            "stats": asdict(self.stats),
        }
        if include_dedications:
            result["dedications"] = [asdict(pair) for pair in self.dedications]
        return result


def _threshold(value: float, name: str) -> tuple[float, Fraction]:
    numeric = float(value)
    if not isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{name} must be finite and between 0 and 1 inclusive")
    # Treat the textual decimal threshold as the intended value.  In particular,
    # ceil(1 / (1 - 0.9)) with binary floats would incorrectly require 11 callers.
    return numeric, Fraction(str(value))


def _at_most_exact_boundary(
    value: float, denominators: list[int], cutoff: Fraction
) -> bool:
    """Compare a reciprocal sum without changing an inclusive boundary.

    Fast floating-point evaluation suffices away from the cutoff.  Only at a
    binary-rounding boundary do we sum exact rational values.  This is not an
    epsilon that changes the paper's decision rule.
    """
    limit = float(cutoff)
    rounding_margin = 8 * max(ulp(value), ulp(limit))
    if value < limit - rounding_margin:
        return True
    if value > limit + rounding_margin:
        return False
    return sum((Fraction(1, denominator) for denominator in denominators), Fraction()) <= cutoff


def detect_omnipresent(
    classes: Iterable[str],
    member_edges: Iterable[MemberEdge],
    *,
    member_owners: Mapping[str, str] | None = None,
    usage_threshold: float = 0.85,
    cardinality_threshold: float = 0.90,
) -> UEResult:
    """Detect all omnipresent classes once on the original scoped graph.

    ``member_edges`` accepts either dictionaries with ``source_class``,
    ``source_member``, ``target_class``, ``target_member``, or two-tuples of
    globally unique member IDs.  The tuple form requires ``member_owners``.
    Owners are normalized project class names.  A missing tuple owner is an
    input error; an explicitly out-of-scope owner is filtered as external.

    Exact member pairs and class-to-target-member pairs are deduplicated
    separately.  Two different methods of A calling the same B method increase
    that method's xm_fanin twice but contribute it only once to D_M(A, B).

    Hash aggregation is linear in the number of distinct member references,
    class pairs, and classes.  Deterministic output sorting additionally costs
    O(C log C + N log N), for C class pairs and N classes.  No dense graph,
    shortest-path enumeration, iteration, or post-removal recomputation occurs.
    """
    usage_float, usage_fraction = _threshold(usage_threshold, "usage_threshold")
    cardinality_float, cardinality_fraction = _threshold(
        cardinality_threshold, "cardinality_threshold"
    )
    class_set = set(classes)
    if any(not isinstance(name, str) or not name for name in class_set):
        raise ValueError("classes must contain nonempty class names")

    owners: dict[str, str] = {}
    source_members_by_target: dict[str, set[str]] = defaultdict(set)
    caller_classes_by_target: dict[str, set[str]] = defaultdict(set)
    target_members_by_class: dict[str, set[str]] = defaultdict(set)
    input_count = excluded_external = excluded_intraclass = duplicate_count = 0

    for edge in member_edges:
        input_count += 1
        if isinstance(edge, Mapping):
            try:
                source = edge["source_member"]
                target = edge["target_member"]
                source_class = edge["source_class"]
                target_class = edge["target_class"]
            except KeyError as exc:
                raise ValueError(f"member edge is missing {exc.args[0]!r}") from exc
        else:
            if member_owners is None:
                raise ValueError("tuple member edges require a member_owners mapping")
            if isinstance(edge, (str, bytes)) or len(edge) != 2:
                raise ValueError("member edges must be pairs of member identifiers")
            source, target = edge
            try:
                source_class = member_owners[source]
                target_class = member_owners[target]
            except KeyError as exc:
                raise ValueError(f"owner missing for member {exc.args[0]!r}") from exc

        if any(not isinstance(item, str) or not item for item in (source, target, source_class, target_class)):
            raise ValueError("member IDs and owner class names must be nonempty strings")
        if source_class not in class_set or target_class not in class_set:
            excluded_external += 1
            continue
        if source_class == target_class:
            excluded_intraclass += 1
            continue

        for member, owner in ((source, source_class), (target, target_class)):
            previous = owners.setdefault(member, owner)
            if previous != owner:
                raise ValueError(
                    f"member ID {member!r} has conflicting owners {previous!r} and {owner!r}; "
                    "use globally unique member identifiers"
                )

        callers = source_members_by_target[target]
        if source in callers:
            duplicate_count += 1
            continue
        callers.add(source)
        caller_classes_by_target[target].add(source_class)
        target_members_by_class[target_class].add(target)

    # Each target member contributes once for each distinct CALLER CLASS;
    # the denominator still counts all distinct caller MEMBERS outside B.
    pair_denominators: dict[tuple[str, str], list[int]] = defaultdict(list)
    callers_by_class: dict[str, set[str]] = defaultdict(set)
    for target, caller_members in source_members_by_target.items():
        target_class = owners[target]
        denominator = len(caller_members) * len(target_members_by_class[target_class])
        for caller_class in caller_classes_by_target[target]:
            pair_denominators[caller_class, target_class].append(denominator)
            callers_by_class[target_class].add(caller_class)

    maximum: dict[str, float] = {}
    strongest: dict[str, str] = {}
    equality_passed: dict[str, bool] = defaultdict(lambda: True)
    dedication_rows: list[UEDedication] = []
    for (source_class, target_class), denominators in sorted(pair_denominators.items()):
        dedication = fsum(1 / denominator for denominator in denominators)
        dedication_rows.append(
            UEDedication(source_class, target_class, len(denominators), dedication)
        )
        if target_class not in maximum or dedication > maximum[target_class]:
            maximum[target_class] = dedication
            strongest[target_class] = source_class
        if not _at_most_exact_boundary(dedication, denominators, 1 - usage_fraction):
            equality_passed[target_class] = False

    score_rows: list[UEClassScore] = []
    for class_name in sorted(class_set):
        fanin = len(callers_by_class.get(class_name, ()))
        member_count = len(target_members_by_class.get(class_name, ()))
        if fanin == 0:
            # The paper leaves max(empty) and 1/0 undefined.  Keep the class;
            # no outside member-use evidence cannot establish omnipresence.
            score_rows.append(
                UEClassScore(class_name, 0, 0, None, None, None, None, False, False, False,
                             "no_external_member_use")
            )
            continue
        max_dedication = maximum[class_name]
        equality = 1.0 - max_dedication
        cardinality = 1.0 - 1.0 / fanin
        passes_e = equality_passed[class_name]
        passes_c = fanin * (1 - cardinality_fraction) >= 1
        is_omnipresent = passes_e and passes_c
        if not passes_e:
            reason = "usage_equality_below_threshold"
        elif not passes_c:
            reason = "cardinality_below_threshold"
        else:
            reason = "usage_equality_and_cardinality_at_or_above_thresholds"
        score_rows.append(
            UEClassScore(class_name, fanin, member_count, max_dedication, equality, cardinality,
                         strongest[class_name], passes_e, passes_c, is_omnipresent, reason)
        )

    return UEResult(
        usage_float,
        cardinality_float,
        tuple(score_rows),
        tuple(dedication_rows),
        UEStats(
            classes=len(class_set),
            input_member_edges=input_count,
            excluded_external_edges=excluded_external,
            excluded_intraclass_edges=excluded_intraclass,
            duplicate_member_edges=duplicate_count,
            unique_member_edges=sum(len(sources) for sources in source_members_by_target.values()),
            referenced_target_members=len(source_members_by_target),
            class_pairs=len(pair_denominators),
        ),
    )
