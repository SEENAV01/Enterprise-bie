"""RE-TEMP-001: explicit time axes, BCE/CE conversion and uncertain chronologies."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import date
import re

from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs

TASK_ID = "BIE-RE-TEMP-001"


@dataclass(frozen=True)
class TimeSpan:
    """Closed uncertainty interval for an event time (not its duration).

historical_year uses astronomical ticks: 1 BCE = 0, 1 CE = 1.
gregorian_day uses datetime.date ordinals. Open bounds represent missing evidence.
"""
    earliest: int | None
    latest: int | None
    axis: str = "historical_year"

    def __post_init__(self):
        if self.axis not in {"historical_year", "gregorian_day"}:
            raise ValueError("Unsupported temporal axis")
        for bound in (self.earliest, self.latest):
            if bound is not None and type(bound) is not int:
                raise ValueError("Temporal bounds must be integer ticks or None")
            if bound is not None and self.axis == "gregorian_day" and not 1 <= bound <= date.max.toordinal():
                raise ValueError("Gregorian day outside supported calendar")
        if self.earliest is not None and self.latest is not None and self.earliest > self.latest:
            raise ValueError("Reversed temporal uncertainty bounds")


@dataclass(frozen=True)
class Event:
    event_id: str
    label: str
    time: TimeSpan
    evidence_ids: tuple[str, ...]


def year(value: str) -> TimeSpan:
    if not isinstance(value, str):
        raise ValueError("Year must be a source label")
    match = re.fullmatch(r"([1-9][0-9]{0,8})(?:\s+(BCE|BC|CE|AD))?", value.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Expected positive historical year with optional BCE/CE; there is no historical year zero")
    number = int(match[1])
    tick = 1 - number if (match[2] or "CE").upper() in {"BCE", "BC"} else number
    return TimeSpan(tick, tick)


def calendar_date(value: str) -> TimeSpan:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("Expected YYYY-MM-DD Gregorian date")
    tick = date.fromisoformat(value).toordinal()
    return TimeSpan(tick, tick, "gregorian_day")


def validate_events(events, refs):
    events, refs = tuple(events), evidence(refs)
    if not events:
        raise ValueError("At least one event required")
    ids, axes = set(), set()
    for event in events:
        identifier(event.event_id, "event id"); identifier(event.label, "event label")
        if not isinstance(event.time, TimeSpan):
            raise ValueError("Event requires a TimeSpan")
        if event.event_id in ids:
            raise ValueError("Duplicate event id")
        ids.add(event.event_id); axes.add(event.time.axis)
        require_refs(event.evidence_ids, refs)
    if len(axes) != 1:
        raise ValueError("Time axes cannot be mixed without an explicit conversion")
    return tuple(sorted(events, key=lambda x: x.event_id)), refs


def relation(a: TimeSpan, b: TimeSpan) -> str:
    if a.axis != b.axis:
        raise ValueError("Incompatible time axes")
    if a.latest is not None and b.earliest is not None and a.latest < b.earliest:
        return "before"
    if b.latest is not None and a.earliest is not None and b.latest < a.earliest:
        return "after"
    if a.earliest is not None and a.earliest == a.latest == b.earliest == b.latest:
        return "simultaneous"
    return "indeterminate"


def chronology(events, refs):
    events, refs = validate_events(events, refs)
    before, simultaneous, unresolved = [], [], []
    for i, a in enumerate(events):
        for b in events[i + 1:]:
            r = relation(a.time, b.time)
            if r == "before": before.append([a.event_id, b.event_id])
            elif r == "after": before.append([b.event_id, a.event_id])
            elif r == "simultaneous": simultaneous.append([a.event_id, b.event_id])
            else: unresolved.append([a.event_id, b.event_id])
    display = sorted(events, key=lambda x: (x.time.earliest is None, x.time.earliest or 0, x.event_id))
    value = {"axis": events[0].time.axis, "display_order": [e.event_id for e in display], "proven_before": sorted(before), "simultaneous": sorted(simultaneous), "unresolved_pairs": sorted(unresolved)}
    return inference(TASK_ID, "temporal.chronology", {"events": [asdict(e) for e in events]}, value, refs, status="AMBIGUOUS" if unresolved else "RESOLVED", assumptions=("Intervals express uncertainty in event dates, not event duration", "Display order is deterministic presentation only; proven_before contains established ordering"), uncertainty=("Overlapping or open date ranges do not establish an event order",) if unresolved else ())
