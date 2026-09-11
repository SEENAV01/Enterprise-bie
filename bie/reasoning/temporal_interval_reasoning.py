"""RE-TEMP-004: evidence-grounded interval algebra for uncertain event intervals."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import identifier, inference, require_refs, evidence

TASK_ID = "BIE-RE-TEMP-004"

@dataclass(frozen=True)
class TemporalInterval:
    interval_id: str
    label: str
    span: TimeSpan
    evidence_ids: tuple[str, ...]


def _validate(intervals, refs):
    refs = evidence(refs); intervals = tuple(intervals)
    if not intervals: raise ValueError("At least one temporal interval required")
    ids=set(); axes=set()
    for item in intervals:
        identifier(item.interval_id,"interval id"); identifier(item.label,"interval label")
        if not isinstance(item.span, TimeSpan): raise ValueError("Interval requires TimeSpan")
        if item.span.earliest is None or item.span.latest is None: raise ValueError("Interval algebra requires closed bounds")
        if item.interval_id in ids: raise ValueError("Duplicate interval id")
        ids.add(item.interval_id); axes.add(item.span.axis); require_refs(item.evidence_ids, refs)
    if len(axes)!=1: raise ValueError("Temporal interval axes cannot be mixed")
    return tuple(sorted(intervals,key=lambda x:x.interval_id)), refs


def interval_relation(a: TimeSpan,b: TimeSpan)->str:
    if a.axis!=b.axis: raise ValueError("Incompatible time axes")
    if None in (a.earliest,a.latest,b.earliest,b.latest): raise ValueError("Closed bounds required")
    a1,a2,b1,b2=a.earliest,a.latest,b.earliest,b.latest
    if a2 < b1: return "before"
    if a2 == b1 and a1 < a2 < b2: return "meets"
    if a1 < b1 < a2 < b2: return "overlaps"
    if a1 == b1 and a2 < b2: return "starts"
    if b1 < a1 and a2 < b2: return "during"
    if b1 < a1 and a2 == b2: return "finishes"
    if a1 == b1 and a2 == b2: return "equal"
    inverse={"before":"after","meets":"met_by","overlaps":"overlapped_by","starts":"started_by","during":"contains","finishes":"finished_by"}
    r=interval_relation(b,a)
    return inverse[r]


def interval_matrix(intervals, refs):
    intervals,refs=_validate(intervals,refs)
    rows=[]
    for i,a in enumerate(intervals):
        for b in intervals[i+1:]:
            rows.append({"left":a.interval_id,"right":b.interval_id,"relation":interval_relation(a.span,b.span),"evidence_ids":sorted(set(a.evidence_ids+b.evidence_ids))})
    return inference(TASK_ID,"temporal.interval_algebra",{"intervals":[asdict(x) for x in intervals]}, {"axis":intervals[0].span.axis,"relations":rows}, refs, assumptions=("Intervals are closed evidence-supplied temporal extents","Relations describe interval extents, not causal order"))
