from dataclasses import dataclass
from .temporal_common import *

@dataclass(frozen=True)
class NarrationCue:
    cue_id:str
    start_ms:int
    end_ms:int
    text_ref:str
    narration_revision:int
    target_ids:tuple[str,...]=()
    def __post_init__(self):
        object.__setattr__(self,"cue_id",tok(self.cue_id,"cue_id"))
        object.__setattr__(self,"start_ms",posint(self.start_ms,"start_ms",allow_zero=True))
        object.__setattr__(self,"end_ms",posint(self.end_ms,"end_ms"))
        if self.end_ms<=self.start_ms: raise TemporalIRError("cue end must exceed start")
        object.__setattr__(self,"text_ref",tok(self.text_ref,"text_ref"))
        object.__setattr__(self,"narration_revision",posint(self.narration_revision,"narration_revision"))
        object.__setattr__(self,"target_ids",tuple(tok(x,"target_id") for x in self.target_ids))

def validate_narration_cues(cues,scene_duration_ms,narration_revision):
    cues=tuple(cues);scene_duration_ms=posint(scene_duration_ms,"scene_duration_ms")
    blockers=[]
    if len({c.cue_id for c in cues})!=len(cues): raise TemporalIRError("duplicate cue id")
    for c in cues:
        if c.end_ms>scene_duration_ms: blockers.append("cue_exceeds_scene:"+c.cue_id)
        if c.narration_revision!=narration_revision: blockers.append("stale_narration_revision:"+c.cue_id)
    return tuple(sorted(blockers))
