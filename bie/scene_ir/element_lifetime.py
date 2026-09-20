from dataclasses import dataclass
from .temporal_common import *

@dataclass(frozen=True)
class ElementLifetime:
    element_id:str
    born_ms:int
    dead_ms:int
    visibility_policy:str="visible"
    def __post_init__(self):
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        object.__setattr__(self,"born_ms",posint(self.born_ms,"born_ms",allow_zero=True))
        object.__setattr__(self,"dead_ms",posint(self.dead_ms,"dead_ms"))
        if self.dead_ms<=self.born_ms:
            raise TemporalIRError("dead_ms must exceed born_ms")
        if self.visibility_policy not in {"visible","hidden_before_birth","remove_after_death"}:
            raise TemporalIRError("unsupported visibility_policy")

def validate_lifetimes(lifetimes,scene_duration_ms):
    scene_duration_ms=posint(scene_duration_ms,"scene_duration_ms")
    lifetimes=tuple(lifetimes)
    if len({x.element_id for x in lifetimes})!=len(lifetimes):
        raise TemporalIRError("duplicate lifetime element")
    out=[]
    for x in lifetimes:
        if x.dead_ms>scene_duration_ms:
            out.append("lifetime_exceeds_scene:"+x.element_id)
    return tuple(out)
