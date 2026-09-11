"""RE-TEMP-011: evidence-grounded alignment of source-defined periodization schemes."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.periodization_reasoning import Period
from bie.reasoning.grounded_result import evidence, inference, require_refs
TASK_ID="BIE-RE-TEMP-011"

@dataclass(frozen=True)
class PeriodAlignment:
    left_period_id: str
    right_period_id: str
    evidence_ids: tuple[str, ...]


def align_period_schemes(periods, alignments, refs):
    refs=evidence(refs); periods=tuple(periods); alignments=tuple(alignments)
    if not periods: raise ValueError("Periods required")
    by_id={}
    for p in periods:
        if not isinstance(p,Period): raise ValueError("Expected Period")
        if p.period_id in by_id: raise ValueError("Duplicate period id")
        require_refs(p.evidence_ids,refs); by_id[p.period_id]=p
    if len({p.axis for p in periods})!=1: raise ValueError("Period axes cannot be mixed")
    rows=[]; seen=set()
    for a in sorted(alignments,key=lambda x:(x.left_period_id,x.right_period_id)):
        if not isinstance(a,PeriodAlignment): raise ValueError("Expected PeriodAlignment")
        if a.left_period_id not in by_id or a.right_period_id not in by_id or a.left_period_id==a.right_period_id: raise ValueError("Alignment endpoints must be known distinct periods")
        left,right=by_id[a.left_period_id],by_id[a.right_period_id]
        if left.scheme_id==right.scheme_id: raise ValueError("Alignment is only for distinct schemes")
        key=tuple(sorted((a.left_period_id,a.right_period_id)))
        if key in seen: raise ValueError("Duplicate alignment")
        seen.add(key); require_refs(a.evidence_ids,refs)
        overlap=max(0,min(left.end,right.end)-max(left.start,right.start))
        union=max(left.end,right.end)-min(left.start,right.start)
        rows.append({"left_period_id":a.left_period_id,"right_period_id":a.right_period_id,"boundary_overlap_ticks":overlap,"boundary_union_ticks":union,"boundary_overlap_ratio":overlap/union if union else 0.0,"evidence_ids":sorted(a.evidence_ids)})
    status="RESOLVED" if alignments else "AMBIGUOUS"
    return inference(TASK_ID,"temporal.scheme_alignment",{"periods":[asdict(p) for p in sorted(periods,key=lambda p:p.period_id)],"alignments":[asdict(a) for a in sorted(alignments,key=lambda a:(a.left_period_id,a.right_period_id))]}, {"axis":periods[0].axis,"alignments":rows}, refs,status=status,assumptions=("Supplied alignment asserts comparability, not identity of historiographical meaning",),uncertainty=("No cross-scheme alignment evidence was supplied",) if not alignments else ())
