from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class RelativeConstraint:
    constraint_id:str
    subject_id:str
    relation:str
    reference_id:str
    gap:float=0.0
    priority:int=100
    def __post_init__(self):
        object.__setattr__(self,"constraint_id",tok(self.constraint_id,"constraint_id"))
        object.__setattr__(self,"subject_id",tok(self.subject_id,"subject_id"))
        object.__setattr__(self,"reference_id",tok(self.reference_id,"reference_id"))
        if self.relation not in {"left_of","right_of","above","below","inside","overlap","near"}:
            raise SpaceIRError("unsupported relative relation")
        object.__setattr__(self,"gap",num(self.gap,"gap"))
        if self.gap<0:raise SpaceIRError("gap cannot be negative")
        if isinstance(self.priority,bool) or not isinstance(self.priority,int) or self.priority<0:
            raise SpaceIRError("priority invalid")
def validate_relative_constraints(constraints):
    cs=tuple(constraints)
    ids=[c.constraint_id for c in cs]
    if len(ids)!=len(set(ids)):raise SpaceIRError("duplicate constraint id")
    contradictions=[]
    pairs={(c.subject_id,c.relation,c.reference_id) for c in cs}
    opposites={"left_of":"right_of","right_of":"left_of","above":"below","below":"above"}
    for c in cs:
        opp=opposites.get(c.relation)
        if opp and (c.subject_id,opp,c.reference_id) in pairs:
            contradictions.append(c.constraint_id)
    return tuple(sorted(set(contradictions)))
