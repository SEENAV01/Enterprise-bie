from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class AlignmentConstraint:
    constraint_id:str
    element_ids:tuple[str,...]
    axis:str
    mode:str
    tolerance:float=0.0
    def __post_init__(self):
        object.__setattr__(self,"constraint_id",tok(self.constraint_id,"constraint_id"))
        ids=tuple(tok(x,"element_id") for x in self.element_ids)
        if len(ids)<2 or len(set(ids))!=len(ids):raise SpaceIRError("alignment element_ids invalid")
        object.__setattr__(self,"element_ids",ids)
        if self.axis not in {"x","y"}:raise SpaceIRError("axis must be x or y")
        if self.mode not in {"start","center","end","distribute"}:raise SpaceIRError("unsupported alignment mode")
        object.__setattr__(self,"tolerance",num(self.tolerance,"tolerance"))
        if self.tolerance<0:raise SpaceIRError("negative tolerance")
def alignment_key(c):
    return (c.axis,c.mode,c.element_ids)
