from dataclasses import dataclass, field
from typing import Mapping, Any
from .temporal_common import *

@dataclass(frozen=True)
class TimelineEvent:
    event_id:str
    at_ms:int
    event_type:str
    target_ids:tuple[str,...]
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"event_id",tok(self.event_id,"event_id"))
        object.__setattr__(self,"at_ms",posint(self.at_ms,"at_ms",allow_zero=True))
        object.__setattr__(self,"event_type",tok(self.event_type,"event_type"))
        ids=tuple(tok(x,"target_id") for x in self.target_ids)
        if not ids: raise TemporalIRError("event target required")
        object.__setattr__(self,"target_ids",ids)
        object.__setattr__(self,"payload",dict(self.payload))

def build_event_timeline(events,scene_duration_ms):
    events=tuple(events);scene_duration_ms=posint(scene_duration_ms,"scene_duration_ms")
    if len({e.event_id for e in events})!=len(events): raise TemporalIRError("duplicate event id")
    if any(e.at_ms>scene_duration_ms for e in events): raise TemporalIRError("event outside scene")
    return tuple(sorted(events,key=lambda e:(e.at_ms,e.event_id)))
