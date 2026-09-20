from dataclasses import dataclass,field
from hashlib import sha256
import json
SCHEMA_VERSION="1.0.0"
class AnimationPlanError(ValueError):pass
def _fp(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()
@dataclass(frozen=True)
class AnimationTrack:
    track_id:str;semantic_action:str;target_ids:tuple[str,...];start_ms:int;end_ms:int;source_refs:tuple[str,...];reasoning_refs:tuple[str,...];owner_stage:str="SEM";reduced_motion_variant:str|None=None;payload:dict=field(default_factory=dict)
    def __post_init__(self):
        if not self.track_id or not self.target_ids or not self.source_refs or not self.reasoning_refs:raise AnimationPlanError("track identity/lineage required")
        if self.start_ms<0 or self.end_ms<=self.start_ms:raise AnimationPlanError("track timing invalid")
@dataclass(frozen=True)
class AnimationPlan:
    plan_id:str;schema_version:str;visual_handoff_id:str;visual_plan_fingerprint:str;visual_revision:int;narration_revision:int;target_profile:str;tracks:tuple[AnimationTrack,...];scene_start_ms:int;scene_end_ms:int;source_refs:tuple[str,...];reasoning_refs:tuple[str,...];reduced_motion_requested:bool=False;plan_fingerprint:str="";accepted:bool=False
    def __post_init__(self):
        if self.schema_version!=SCHEMA_VERSION:raise AnimationPlanError("schema mismatch")
        if len(self.visual_plan_fingerprint)!=64:raise AnimationPlanError("bad VIS fingerprint")
        if self.visual_revision<1 or self.narration_revision<1:raise AnimationPlanError("bad revision")
        if not self.tracks or len({t.track_id for t in self.tracks})!=len(self.tracks):raise AnimationPlanError("invalid tracks")
        if self.scene_start_ms<0 or self.scene_end_ms<=self.scene_start_ms:raise AnimationPlanError("bad scene interval")
        if any(t.start_ms<self.scene_start_ms or t.end_ms>self.scene_end_ms for t in self.tracks):raise AnimationPlanError("track outside scene")
        payload={"plan_id":self.plan_id,"schema_version":self.schema_version,"visual_handoff_id":self.visual_handoff_id,"visual_plan_fingerprint":self.visual_plan_fingerprint,"visual_revision":self.visual_revision,"narration_revision":self.narration_revision,"target_profile":self.target_profile,"tracks":[t.__dict__ for t in self.tracks],"scene_start_ms":self.scene_start_ms,"scene_end_ms":self.scene_end_ms,"source_refs":self.source_refs,"reasoning_refs":self.reasoning_refs,"reduced_motion_requested":self.reduced_motion_requested,"accepted":False}
        object.__setattr__(self,"plan_fingerprint",_fp(payload))
