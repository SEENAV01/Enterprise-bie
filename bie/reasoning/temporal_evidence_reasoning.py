"""RE-TEMP-007: conservative fusion of competing evidence-backed temporal spans."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import evidence, identifier, inference, require_refs
TASK_ID="BIE-RE-TEMP-007"

@dataclass(frozen=True)
class TemporalHypothesis:
    hypothesis_id:str
    span:TimeSpan
    evidence_ids:tuple[str,...]


def fuse_temporal_hypotheses(subject_id,hypotheses,refs):
    refs=evidence(refs); identifier(subject_id,"subject id"); hypotheses=tuple(sorted(hypotheses,key=lambda h:h.hypothesis_id))
    if not hypotheses: raise ValueError("At least one temporal hypothesis required")
    axes=set(); seen=set()
    for h in hypotheses:
        identifier(h.hypothesis_id,"hypothesis id"); require_refs(h.evidence_ids,refs)
        if h.hypothesis_id in seen: raise ValueError("Duplicate hypothesis id")
        seen.add(h.hypothesis_id); axes.add(h.span.axis)
        if h.span.earliest is None or h.span.latest is None: raise ValueError("Fusion requires closed hypothesis bounds")
    if len(axes)!=1: raise ValueError("Hypothesis axes cannot be mixed")
    lo=max(h.span.earliest for h in hypotheses); hi=min(h.span.latest for h in hypotheses)
    if lo<=hi:
        value={"subject_id":subject_id,"consensus":{"earliest":lo,"latest":hi,"axis":hypotheses[0].span.axis},"hypothesis_ids":[h.hypothesis_id for h in hypotheses],"conflicting_pairs":[]}
        status="RESOLVED"
        unc=()
    else:
        conflicts=[]
        for i,a in enumerate(hypotheses):
            for b in hypotheses[i+1:]:
                if a.span.latest < b.span.earliest or b.span.latest < a.span.earliest: conflicts.append([a.hypothesis_id,b.hypothesis_id])
        value={"subject_id":subject_id,"consensus":None,"hypothesis_ids":[h.hypothesis_id for h in hypotheses],"conflicting_pairs":sorted(conflicts)}
        status="CONFLICT"; unc=("Evidence-backed temporal hypotheses have no common intersection; no winner is invented",)
    return inference(TASK_ID,"temporal.evidence_fusion",{"subject_id":subject_id,"hypotheses":[asdict(h) for h in hypotheses]},value,refs,status=status,assumptions=("Consensus is the intersection of supplied evidence-backed spans; source authority is not invented",),uncertainty=unc)
