from dataclasses import dataclass, field
from typing import Mapping, Any
from .temporal_common import *

@dataclass(frozen=True)
class AnimationTrackSpec:
    track_id:str
    element_id:str
    action:str
    start_ms:int
    end_ms:int
    easing:str="linear"
    parameters:Mapping[str,Any]=field(default_factory=dict)
    source_refs:tuple[str,...]=()
    reasoning_refs:tuple[str,...]=()
    def __post_init__(self):
        object.__setattr__(self,"track_id",tok(self.track_id,"track_id"))
        object.__setattr__(self,"element_id",tok(self.element_id,"element_id"))
        object.__setattr__(self,"action",tok(self.action,"action"))
        object.__setattr__(self,"start_ms",posint(self.start_ms,"start_ms",allow_zero=True))
        object.__setattr__(self,"end_ms",posint(self.end_ms,"end_ms"))
        if self.end_ms<=self.start_ms: raise TemporalIRError("track end must exceed start")
        if self.easing not in {"linear","ease_in","ease_out","ease_in_out","step","spring"}:
            raise TemporalIRError("unsupported easing")
        if not self.source_refs or not self.reasoning_refs:
            raise TemporalIRError("track source/reasoning lineage required")
        object.__setattr__(self,"parameters",dict(self.parameters))

def validate_tracks(tracks,element_ids,scene_duration_ms):
    tracks=tuple(tracks);valid=set(element_ids);scene_duration_ms=posint(scene_duration_ms,"scene_duration_ms")
    if len({t.track_id for t in tracks})!=len(tracks): raise TemporalIRError("duplicate track id")
    blockers=[]
    for t in tracks:
        if t.element_id not in valid: blockers.append("unknown_element:"+t.track_id)
        if t.end_ms>scene_duration_ms: blockers.append("track_exceeds_scene:"+t.track_id)
    return tuple(sorted(blockers))
