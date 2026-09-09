"""RE-TEMP-003: source-defined period membership with explicit boundary semantics."""
from __future__ import annotations
from dataclasses import asdict, dataclass

from bie.reasoning.chronology_reasoning import TimeSpan, validate_events
from bie.reasoning.grounded_result import identifier, inference, require_refs

TASK_ID = "BIE-RE-TEMP-003"


@dataclass(frozen=True)
class Period:
    period_id: str
    label: str
    start: int
    end: int
    evidence_ids: tuple[str, ...]
    axis: str = "historical_year"
    parent_id: str | None = None
    scheme_id: str = "source_defined"


def periodization(events, periods, refs):
    events, refs = validate_events(events, refs)
    periods = tuple(periods)
    if not periods:
        raise ValueError("Source-defined periods required; boundaries are never invented")
    by_id = {}
    axis = events[0].time.axis
    for p in periods:
        identifier(p.period_id, "period id"); identifier(p.label, "period label"); identifier(p.scheme_id, "scheme id")
        require_refs(p.evidence_ids, refs)
        TimeSpan(p.start, p.end, p.axis)
        if p.start is None or p.end is None or p.start >= p.end or p.axis != axis:
            raise ValueError("Nonempty half-open period on the event time axis required")
        if p.period_id in by_id:
            raise ValueError("Duplicate period id")
        by_id[p.period_id] = p
    for p in periods:
        seen, current = {p.period_id}, p
        while current.parent_id is not None:
            if current.parent_id not in by_id or current.parent_id in seen:
                raise ValueError("Missing parent or cyclic period hierarchy")
            parent = by_id[current.parent_id]
            if parent.scheme_id != current.scheme_id or not parent.start <= current.start < current.end <= parent.end:
                raise ValueError("Nested period must fit its parent in the same scheme")
            seen.add(parent.period_id); current = parent
    siblings = {}
    for p in periods:
        siblings.setdefault((p.scheme_id, p.parent_id), []).append(p)
    overlaps = []
    for group in siblings.values():
        group = sorted(group, key=lambda p: (p.start, p.end, p.period_id))
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if b.start >= a.end: break
                overlaps.append([a.period_id, b.period_id])
    assignments = []
    for event in events:
        lo, hi = event.time.earliest, event.time.latest
        definite, possible = [], []
        for p in sorted(periods, key=lambda p: p.period_id):
            if lo is not None and hi is not None and p.start <= lo <= hi < p.end:
                definite.append(p.period_id)
            if (hi is None or hi >= p.start) and (lo is None or lo < p.end):
                possible.append(p.period_id)
        uncertain = sorted(set(possible) - set(definite))
        status = "AMBIGUOUS" if uncertain else "ASSIGNED" if definite else "UNASSIGNED"
        assignments.append({"event_id": event.event_id, "definite_period_ids": definite, "possible_period_ids": possible, "status": status, "evidence_ids": sorted(set(event.evidence_ids) | {ref for pid in possible for ref in by_id[pid].evidence_ids})})
    ambiguous = bool(overlaps) or any(x["status"] != "ASSIGNED" for x in assignments)
    inputs = {"events": [asdict(x) for x in events], "periods": [asdict(x) for x in sorted(periods, key=lambda p: p.period_id)]}
    return inference(TASK_ID, "temporal.periodization", inputs, {"axis": axis, "boundary_policy": "start_inclusive_end_exclusive", "assignments": assignments, "overlapping_siblings": sorted(overlaps)}, refs, status="AMBIGUOUS" if ambiguous else "RESOLVED", assumptions=("Period boundaries and schemes are supplied by source evidence", "Nested periods may both contain the same event; no preferred historiography is inferred"), uncertainty=("Boundary uncertainty, unassigned events, or overlapping sibling periods require review",) if ambiguous else ())
