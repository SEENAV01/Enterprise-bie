"""RE-TEMP-009: evidence-grounded relative temporal offsets with uncertainty propagation."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-009"

@dataclass(frozen=True)
class RelativeOffset:
    relation_id: str
    anchor_id: str
    target_id: str
    min_offset: int
    max_offset: int
    evidence_ids: tuple[str, ...]


def resolve_relative_time(anchor_id, anchor_span, relation, refs):
    refs=evidence(refs); identifier(anchor_id,"anchor id")
    if not isinstance(anchor_span,TimeSpan): raise ValueError("Anchor requires TimeSpan")
    if not isinstance(relation,RelativeOffset): raise ValueError("Expected RelativeOffset")
    identifier(relation.relation_id,"relation id"); identifier(relation.anchor_id,"relation anchor id"); identifier(relation.target_id,"target id")
    require_refs(relation.evidence_ids,refs)
    if relation.anchor_id != anchor_id: raise ValueError("Relative relation anchor does not match supplied anchor")
    if isinstance(relation.min_offset,bool) or isinstance(relation.max_offset,bool) or not isinstance(relation.min_offset,int) or not isinstance(relation.max_offset,int): raise ValueError("Offsets must be integer ticks")
    if relation.min_offset > relation.max_offset: raise ValueError("Relative offset bounds are reversed")
    lo=None if anchor_span.earliest is None else anchor_span.earliest+relation.min_offset
    hi=None if anchor_span.latest is None else anchor_span.latest+relation.max_offset
    target=TimeSpan(lo,hi,anchor_span.axis)
    status="AMBIGUOUS" if lo is None or hi is None or lo != hi else "RESOLVED"
    value={"anchor_id":anchor_id,"target_id":relation.target_id,"target_span":asdict(target),"offset":{"min":relation.min_offset,"max":relation.max_offset,"unit":"axis_tick"},"relation_evidence_ids":sorted(relation.evidence_ids)}
    return inference(TASK_ID,"temporal.relative_offset",{"anchor_id":anchor_id,"anchor_span":asdict(anchor_span),"relation":asdict(relation)},value,refs,status=status,assumptions=("Relative offsets are interpreted in the supplied temporal axis resolution",),uncertainty=("Anchor or offset uncertainty propagates to the derived target span",) if status=="AMBIGUOUS" else ())
