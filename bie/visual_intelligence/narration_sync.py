from __future__ import annotations
from dataclasses import dataclass
class NarrationSyncError(ValueError):pass
@dataclass(frozen=True)
class Cue:
    cue_id:str;intent_id:str;start_ms:int;end_ms:int;narration_revision:int;cue_type:str
@dataclass(frozen=True)
class VisualBinding:
    visual_id:str;intent_id:str;start_ms:int;end_ms:int;focus:bool;reveal:bool;cue_id:str;narration_revision:int
@dataclass(frozen=True)
class SyncPlan:
    bindings:tuple[VisualBinding,...];narration_revision:int;warnings:tuple[str,...];review_required:bool=True;accepted:bool=False

def bind_visuals(cues,visuals_by_intent,narration_revision,focus_types=("visual","equation","graph","simulation")):
    cs=tuple(cues)
    if any(c.narration_revision!=narration_revision for c in cs):raise NarrationSyncError("stale narration cue revision")
    out=[];warnings=[]
    for c in sorted(cs,key=lambda x:(x.start_ms,x.end_ms,x.cue_id)):
        if c.end_ms<=c.start_ms:raise NarrationSyncError("invalid cue window")
        vids=tuple(visuals_by_intent.get(c.intent_id,()))
        if not vids: warnings.append("unbound_cue:"+c.cue_id);continue
        for idx,v in enumerate(vids):
            out.append(VisualBinding(v,c.intent_id,c.start_ms,c.end_ms,c.cue_type in focus_types,idx==0,c.cue_id,narration_revision))
    # competing focus check
    fs=[b for b in out if b.focus]
    for i,a in enumerate(fs):
        for b in fs[i+1:]:
            if a.visual_id!=b.visual_id and max(a.start_ms,b.start_ms)<min(a.end_ms,b.end_ms):
                warnings.append("competing_focus:"+a.cue_id+":"+b.cue_id)
    return SyncPlan(tuple(out),narration_revision,tuple(sorted(set(warnings))))
