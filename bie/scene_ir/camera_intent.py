from dataclasses import dataclass
from .space_common import *
@dataclass(frozen=True)
class CameraIntent:
    intent_id:str
    mode:str
    target_ids:tuple[str,...]
    framing:str
    motion_allowed:bool=True
    reduced_motion_fallback:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"intent_id",tok(self.intent_id,"intent_id"))
        if self.mode not in {"static","pan","zoom","orbit","follow","rack_focus"}:raise SpaceIRError("unsupported camera mode")
        ids=tuple(tok(x,"target_id") for x in self.target_ids)
        if not ids:raise SpaceIRError("camera target required")
        object.__setattr__(self,"target_ids",ids)
        if self.framing not in {"wide","medium","close","macro","fit_targets"}:raise SpaceIRError("unsupported framing")
        if self.mode!="static" and not self.motion_allowed:raise SpaceIRError("motion mode requested while motion disallowed")
        if self.reduced_motion_fallback is not None:object.__setattr__(self,"reduced_motion_fallback",tok(self.reduced_motion_fallback,"reduced_motion_fallback"))
def require_accessible_camera(intent,reduced_motion_requested):
    if reduced_motion_requested and intent.mode in {"pan","zoom","orbit","follow","rack_focus"} and not intent.reduced_motion_fallback:
        raise SpaceIRError("reduced-motion camera fallback required")
    return True
