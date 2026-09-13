from dataclasses import dataclass
@dataclass(frozen=True)
class MissingPrerequisite:
    concept_id:str; label:str; severity:float; evidence_ids:tuple[str,...]; prerequisite_ids:tuple[str,...]=()
@dataclass(frozen=True)
class BridgeStep:
    order:int; concept_id:str; teaching_goal:str; evidence_ids:tuple[str,...]; exit_score:float
@dataclass(frozen=True)
class BridgePlan:
    steps:tuple[BridgeStep,...]; requires_bridge:bool; confidence:float
def plan_remedial_bridge(missing,severity_threshold=.35,default_exit_score=.8):
    if not 0<=severity_threshold<=1 or not 0<=default_exit_score<=1: raise ValueError('threshold')
    items=tuple(missing); ids=[x.concept_id for x in items]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate concept')
    for x in items:
        if not x.concept_id.strip() or not x.label.strip() or not x.evidence_ids or not 0<=x.severity<=1: raise ValueError('grounded prerequisite')
    sel=[x for x in items if x.severity>=severity_threshold]
    sel.sort(key=lambda x:(len(x.prerequisite_ids),-x.severity,x.concept_id))
    steps=tuple(BridgeStep(i+1,x.concept_id,'Restore prerequisite mastery: '+x.label,tuple(sorted(set(x.evidence_ids))),default_exit_score) for i,x in enumerate(sel))
    conf=min((1-min(.5,x.severity*.25) for x in sel),default=1.0)
    return BridgePlan(steps,bool(steps),conf)
