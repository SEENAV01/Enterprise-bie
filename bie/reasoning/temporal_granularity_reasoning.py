"""RE-TEMP-012: explicit temporal granularity with conservative cross-precision comparison."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.chronology_reasoning import TimeSpan, relation
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-012"

@dataclass(frozen=True)
class GranularTime:
    time_id: str
    span: TimeSpan
    granularity: str
    evidence_ids: tuple[str, ...]

_ALLOWED={"day":1,"month":2,"year":3,"period":4,"unknown":5}

def compare_granular_times(left,right,refs):
    refs=evidence(refs)
    for item in (left,right):
        if not isinstance(item,GranularTime): raise ValueError("Expected GranularTime")
        identifier(item.time_id,"time id"); require_refs(item.evidence_ids,refs)
        if item.granularity not in _ALLOWED: raise ValueError("Unsupported temporal granularity")
    if left.time_id==right.time_id: raise ValueError("Distinct time ids required")
    if left.span.axis!=right.span.axis: raise ValueError("Incompatible time axes")
    rel=relation(left.span,right.span)
    precision="same" if left.granularity==right.granularity else "mixed"
    status="RESOLVED" if rel!="indeterminate" else "AMBIGUOUS"
    value={"left_id":left.time_id,"right_id":right.time_id,"relation":rel,"precision_relation":precision,"left_granularity":left.granularity,"right_granularity":right.granularity,"evidence_ids":sorted(set(left.evidence_ids+right.evidence_ids))}
    unc=[]
    if precision=="mixed": unc.append("Inputs have different declared temporal granularities; no extra precision is invented")
    if rel=="indeterminate": unc.append("Evidence spans do not establish a strict temporal relation")
    return inference(TASK_ID,"temporal.granularity_compare",{"left":asdict(left),"right":asdict(right)},value,refs,status=status,assumptions=("Granularity labels describe source precision and do not narrow supplied spans",),uncertainty=tuple(unc))
