from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .ids import require_id, require_text, require_unique_ids
from .errors import GameContractError

class VisualKind(str,Enum):
    OBJECT='object';VECTOR='vector';GRAPH='graph';MAP='map';TIMELINE='timeline';EQUATION='equation';LABEL='label';MODEL='model';PARTICLE='particle';FIELD='field';BIO_STRUCTURE='bio_structure';FLOW='flow'
class MotionKind(str,Enum): ENTER='enter';EXIT='exit';MOVE='move';ROTATE='rotate';SCALE='scale';MORPH='morph';HIGHLIGHT='highlight';TRACE='trace';STATE_CHANGE='state_change'
class CameraKind(str,Enum): STATIC='static';FOCUS='focus';PAN='pan';TRACK='track';ZOOM='zoom';ORBIT='orbit'

@dataclass(frozen=True)
class VisualEntity:
    entity_id:str; kind:VisualKind; semantic_role:str; source_ref:str|None=None; state_bindings:tuple[str,...]=(); accessible_description:str|None=None
    def validate(self):
        require_id(self.entity_id,'GAME_VISUAL_ID');require_id(self.semantic_role,'GAME_VISUAL_ROLE')
        if type(self.kind) is not VisualKind:raise GameContractError('GAME_VISUAL_KIND')
        require_text(self.accessible_description,'GAME_VISUAL_ACCESSIBILITY')
        if self.source_ref is not None:require_id(self.source_ref,'GAME_VISUAL_SOURCE_REF')
        return self

@dataclass(frozen=True)
class MotionCue:
    cue_id:str; entity_id:str; kind:MotionKind; start_ms:int; duration_ms:int; pedagogical_purpose:str
    def validate(self,entities:set[str]):
        require_id(self.cue_id,'GAME_MOTION_ID');require_id(self.entity_id,'GAME_MOTION_ENTITY');require_text(self.pedagogical_purpose,'GAME_MOTION_PURPOSE')
        if self.entity_id not in entities:raise GameContractError('GAME_MOTION_ENTITY_MISSING')
        if type(self.kind) is not MotionKind:raise GameContractError('GAME_MOTION_KIND')
        if type(self.start_ms) is not int or self.start_ms<0 or type(self.duration_ms) is not int or self.duration_ms<=0:raise GameContractError('GAME_MOTION_TIME')
        return self

@dataclass(frozen=True)
class CameraCue:
    cue_id:str; kind:CameraKind; start_ms:int; duration_ms:int; pedagogical_purpose:str; target_entity_id:str|None=None
    def validate(self,entities:set[str]):
        require_id(self.cue_id,'GAME_CAMERA_ID');require_text(self.pedagogical_purpose,'GAME_CAMERA_PURPOSE')
        if type(self.kind) is not CameraKind:raise GameContractError('GAME_CAMERA_KIND')
        if self.kind!=CameraKind.STATIC and not self.target_entity_id:raise GameContractError('GAME_CAMERA_TARGET_REQUIRED')
        if self.target_entity_id is not None and self.target_entity_id not in entities:raise GameContractError('GAME_CAMERA_TARGET_MISSING')
        if self.start_ms<0 or self.duration_ms<=0:raise GameContractError('GAME_CAMERA_TIME')
        return self

@dataclass(frozen=True)
class VisualExperienceContract:
    entities:tuple[VisualEntity,...]; motion:tuple[MotionCue,...]=(); camera:tuple[CameraCue,...]=(); background_role:str='supportive'
    def validate(self):
        if not self.entities:raise GameContractError('GAME_VISUAL_ENTITIES_REQUIRED')
        ids=[e.entity_id for e in self.entities];require_unique_ids(ids,'GAME_VISUAL_DUPLICATE');s=set(ids)
        for e in self.entities:e.validate()
        require_unique_ids([m.cue_id for m in self.motion],'GAME_MOTION_DUPLICATE');require_unique_ids([c.cue_id for c in self.camera],'GAME_CAMERA_DUPLICATE')
        for m in self.motion:m.validate(s)
        for c in self.camera:c.validate(s)
        if self.background_role not in {'supportive','contextual','none'}:raise GameContractError('GAME_BACKGROUND_ROLE')
        return self
