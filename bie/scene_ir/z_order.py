from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class ZOrderEntry:
    element_id:str
    z_index:int
    layer:str="content"
    def __post_init__(self):
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        if isinstance(self.z_index,bool) or not isinstance(self.z_index,int):raise SpaceIRError("z_index must be int")
        if self.layer not in {"background","content","overlay","ui"}:raise SpaceIRError("unsupported layer")
def resolve_z_order(entries):
    entries=tuple(entries)
    if len({e.element_id for e in entries})!=len(entries):raise SpaceIRError("duplicate z-order element")
    rank={"background":0,"content":1,"overlay":2,"ui":3}
    return tuple(sorted(entries,key=lambda e:(rank[e.layer],e.z_index,e.element_id)))
