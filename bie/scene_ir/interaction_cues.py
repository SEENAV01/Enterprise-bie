from dataclasses import dataclass, field
from typing import Mapping, Any
from .temporal_common import *

@dataclass(frozen=True)
class InteractionCue:
    cue_id:str
    at_ms:int
    interaction_id:str
    target_ids:tuple[str,...]
    mode:str
    blocking:bool=False
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"cue_id",tok(self.cue_id,"cue_id"))
        object.__setattr__(self,"at_ms",posint(self.at_ms,"at_ms",allow_zero=True))
        object.__setattr__(self,"interaction_id",tok(self.interaction_id,"interaction_id"))
        ids=tuple(tok(x,"target_id") for x in self.target_ids)
        if not ids: raise TemporalIRError("interaction target required")
        object.__setattr__(self,"target_ids",ids)
        if self.mode not in {"tap","drag","hover","choice","scrub","keyboard","simulation_control"}:
            raise TemporalIRError("unsupported interaction mode")
        object.__setattr__(self,"payload",dict(self.payload))

def validate_interaction_cues(cues,scene_duration_ms,known_interaction_ids):
    cues=tuple(cues);scene_duration_ms=posint(scene_duration_ms,"scene_duration_ms")
    known=set(known_interaction_ids);blockers=[]
    if len({c.cue_id for c in cues})!=len(cues): raise TemporalIRError("duplicate interaction cue")
    for c in cues:
        if c.at_ms>scene_duration_ms: blockers.append("interaction_cue_outside_scene:"+c.cue_id)
        if c.interaction_id not in known: blockers.append("unknown_interaction:"+c.cue_id)
    return tuple(sorted(blockers))
