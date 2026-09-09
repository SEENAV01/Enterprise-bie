from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

class SceneIRContractError(ValueError):
    pass

CORE_ELEMENT_KINDS:Set[str]={
"text","equation","shape","vector","diagram","graph","chart","map","timeline",
"image","video","audio_visualizer","simulation","model_2d","model_3d","annotation",
"callout","highlight","particle_system","custom_component"
}
ANIMATION_KINDS:Set[str]={
"enter","exit","transform","emphasize","trace","reveal","morph","camera",
"simulation_state","opacity","scale","translate","rotate","path_follow","custom"
}

@dataclass(frozen=True)
class TimeRange:
    start:float
    end:float
    def validate(self, container:Optional["TimeRange"]=None)->None:
        if self.start<0 or self.end<=self.start:
            raise SceneIRContractError("invalid time range")
        if container and (self.start<container.start or self.end>container.end):
            raise SceneIRContractError("time range outside container")

@dataclass(frozen=True)
class SpatialIntent:
    x:Optional[float]=None; y:Optional[float]=None
    width:Optional[float]=None; height:Optional[float]=None
    anchor:Optional[str]=None
    relative_to:Optional[str]=None
    constraints:List[str]=field(default_factory=list)
    z_index:int=0
    def validate(self)->None:
        for n,v in (("x",self.x),("y",self.y),("width",self.width),("height",self.height)):
            if v is not None and not 0<=v<=1: raise SceneIRContractError(f"{n} outside normalized range")
        if self.width is not None and self.width==0: raise SceneIRContractError("width cannot be zero")
        if self.height is not None and self.height==0: raise SceneIRContractError("height cannot be zero")

@dataclass(frozen=True)
class AnimationTrack:
    animation_id:str
    kind:str
    time:TimeRange
    parameters:Dict[str,Any]=field(default_factory=dict)
    semantic_purpose:Optional[str]=None
    def validate(self, lifetime:TimeRange)->None:
        if not self.animation_id: raise SceneIRContractError("animation_id required")
        if self.kind not in ANIMATION_KINDS: raise SceneIRContractError(f"unsupported animation kind {self.kind}")
        self.time.validate(lifetime)

@dataclass(frozen=True)
class InteractionBinding:
    event:str
    action:str
    target_id:Optional[str]=None
    parameters:Dict[str,Any]=field(default_factory=dict)
    def validate(self)->None:
        if not self.event or not self.action: raise SceneIRContractError("interaction event/action required")

@dataclass(frozen=True)
class Accessibility:
    label:Optional[str]=None
    description:Optional[str]=None
    decorative:bool=False
    def validate(self, meaningful:bool)->None:
        if meaningful and not self.decorative and not (self.label or self.description):
            raise SceneIRContractError("meaningful visual element requires accessibility text")

@dataclass(frozen=True)
class SceneElement:
    element_id:str
    kind:str
    semantic_role:str
    lifetime:TimeRange
    spatial:SpatialIntent
    content:Dict[str,Any]=field(default_factory=dict)
    animations:List[AnimationTrack]=field(default_factory=list)
    interactions:List[InteractionBinding]=field(default_factory=list)
    concept_refs:List[str]=field(default_factory=list)
    learning_objective_refs:List[str]=field(default_factory=list)
    reasoning_decision_refs:List[str]=field(default_factory=list)
    source_artifact_refs:List[str]=field(default_factory=list)
    asset_refs:List[str]=field(default_factory=list)
    accessibility:Accessibility=field(default_factory=Accessibility)
    compiler_capabilities:List[str]=field(default_factory=list)

    def validate(self, scene_time:TimeRange)->None:
        if not self.element_id or not self.semantic_role: raise SceneIRContractError("element id/semantic role required")
        if self.kind not in CORE_ELEMENT_KINDS: raise SceneIRContractError(f"unsupported element kind {self.kind}")
        self.lifetime.validate(scene_time); self.spatial.validate()
        meaningful=self.semantic_role not in {"decoration","background"}
        self.accessibility.validate(meaningful)
        for a in self.animations:a.validate(self.lifetime)
        for i in self.interactions:i.validate()
        if meaningful and not (self.concept_refs or self.learning_objective_refs or self.reasoning_decision_refs or self.source_artifact_refs):
            raise SceneIRContractError("meaningful element must link to educational/evidence semantics")

@dataclass(frozen=True)
class Scene:
    scene_id:str
    title:str
    duration_seconds:float
    purpose:str
    elements:List[SceneElement]
    reasoning_decision_refs:List[str]=field(default_factory=list)
    learning_objective_refs:List[str]=field(default_factory=list)
    audio_plan:Dict[str,Any]=field(default_factory=dict)
    camera_plan:Dict[str,Any]=field(default_factory=dict)
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.scene_id or not self.purpose or self.duration_seconds<=0:
            raise SceneIRContractError("valid scene id/purpose/duration required")
        ids=[e.element_id for e in self.elements]
        if len(ids)!=len(set(ids)):raise SceneIRContractError("duplicate element_id")
        bounds=TimeRange(0,self.duration_seconds)
        for e in self.elements:e.validate(bounds)
        idset=set(ids)
        for e in self.elements:
            if e.spatial.relative_to and e.spatial.relative_to not in idset:
                raise SceneIRContractError(f"missing relative_to target {e.spatial.relative_to}")
            for i in e.interactions:
                if i.target_id and i.target_id not in idset:
                    raise SceneIRContractError(f"missing interaction target {i.target_id}")

@dataclass(frozen=True)
class SceneDocument:
    scene_ir_version:str
    document_id:str
    scenes:List[Scene]
    canvas_aspect_ratio:str="16:9"
    target_capabilities:List[str]=field(default_factory=list)
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self)->None:
        if not self.scene_ir_version or not self.document_id:raise SceneIRContractError("version/document_id required")
        ids=[s.scene_id for s in self.scenes]
        if len(ids)!=len(set(ids)):raise SceneIRContractError("duplicate scene_id")
        if not self.scenes:raise SceneIRContractError("SceneDocument requires scenes")
        for s in self.scenes:s.validate()
