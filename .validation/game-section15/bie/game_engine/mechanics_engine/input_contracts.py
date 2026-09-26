from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Mapping
from ..ids import require_id
from .errors import MechanicError

@dataclass(frozen=True)
class ClassificationItem:
    item_id:str;category:str
    def validate(self):require_id(self.item_id,'GAME_MECH_ITEM_ID');require_id(self.category,'GAME_MECH_ITEM_CATEGORY');return self
    @classmethod
    def from_mapping(cls,v):
        if not isinstance(v,Mapping) or set(('id','class'))-set(v):raise MechanicError('GAME_MECH_CLASSIFY_ITEMS')
        return cls(v['id'],v['class']).validate()
@dataclass(frozen=True)
class ModelPart:
    part_id:str;requires:tuple[str,...]
    def validate(self):require_id(self.part_id,'GAME_MECH_PART_ID');[require_id(x,'GAME_MECH_PART_DEP') for x in self.requires];return self
    @classmethod
    def from_mapping(cls,v):
        if not isinstance(v,Mapping) or 'id' not in v:raise MechanicError('GAME_MECH_MODEL_PART')
        return cls(v['id'],tuple(v.get('requires',()))).validate()
@dataclass(frozen=True)
class SimulationModel:
    kind:str;input_value:float;coefficient:float;offset:float
    def validate(self):
        if self.kind!='linear':raise MechanicError('GAME_MECH_SIMULATION_MODEL')
        for x in (self.input_value,self.coefficient,self.offset):
            if type(x) not in (int,float):raise MechanicError('GAME_MECH_SIMULATION_PARAMETER')
        return self
    @classmethod
    def from_mapping(cls,v):
        if not isinstance(v,Mapping) or v.get('kind')!='linear' or set(v.get('parameters',{}))!={'coefficient','offset'}:raise MechanicError('GAME_MECH_SIMULATION_MODEL')
        return cls('linear',float(v.get('input',0)),float(v['parameters']['coefficient']),float(v['parameters']['offset'])).validate()
@dataclass(frozen=True)
class TimelineEvent:
    event_id:str;time:float
    def validate(self):require_id(self.event_id,'GAME_MECH_TIMELINE_ID');
    @classmethod
    def from_mapping(cls,v):
        if not isinstance(v,Mapping) or 'id' not in v or 'time' not in v or type(v['time']) not in (int,float):raise MechanicError('GAME_MECH_TIMELINE_EVENT')
        x=cls(v['id'],float(v['time']));require_id(x.event_id,'GAME_MECH_TIMELINE_ID');return x
@dataclass(frozen=True)
class SourcedMapLocation:
    name:str;lat:float;lon:float;source_ref:str
    def validate(self):
        require_id(self.name,'GAME_MECH_MAP_NAME');require_id(self.source_ref,'GAME_MECH_MAP_SOURCE')
        if not -90<=self.lat<=90 or not -180<=self.lon<=180:raise MechanicError('GAME_MECH_MAP_COORDINATE')
        return self
    @classmethod
    def from_mapping(cls,name,v):
        if not isinstance(v,Mapping) or 'coord' not in v or 'source_ref' not in v or not isinstance(v['coord'],(tuple,list)) or len(v['coord'])!=2:raise MechanicError('GAME_MECH_MAP_PROVENANCE')
        return cls(name,float(v['coord'][0]),float(v['coord'][1]),v['source_ref']).validate()
@dataclass(frozen=True)
class DiagnosticStep:
    step_id:str;actual:Any;expected:Any;evidence_ref:str
    def validate(self):require_id(self.step_id,'GAME_MECH_DIAGNOSE_ID');require_id(self.evidence_ref,'GAME_MECH_DIAGNOSE_EVIDENCE');return self
    @classmethod
    def from_mapping(cls,v,index):
        if not isinstance(v,Mapping) or set(('actual','expected','evidence_ref'))-set(v):raise MechanicError('GAME_MECH_DIAGNOSE_STEP_SCHEMA')
        return cls(str(v.get('id',f'step:{index}')),v['actual'],v['expected'],v['evidence_ref']).validate()
@dataclass(frozen=True)
class RetrievalItem:
    item_id:str;prompt_ref:str;answer_ref:str;evidence_ref:str
    def validate(self):
        for x,c in ((self.item_id,'GAME_MECH_RETRIEVAL_ID'),(self.prompt_ref,'GAME_MECH_RETRIEVAL_PROMPT'),(self.answer_ref,'GAME_MECH_RETRIEVAL_ANSWER'),(self.evidence_ref,'GAME_MECH_RETRIEVAL_EVIDENCE')):require_id(x,c)
        return self
    @classmethod
    def from_mapping(cls,v):
        if not isinstance(v,Mapping) or set(('id','prompt_ref','answer_ref','evidence_ref'))-set(v):raise MechanicError('GAME_MECH_RETRIEVAL_ITEM')
        return cls(v['id'],v['prompt_ref'],v['answer_ref'],v['evidence_ref']).validate()
@dataclass(frozen=True)
class ResourceBound:
    resource_id:str;minimum:float;maximum:float
    def validate(self):
        require_id(self.resource_id,'GAME_MECH_RESOURCE_ID')
        if type(self.minimum) not in (int,float) or type(self.maximum) not in (int,float) or self.minimum>self.maximum:raise MechanicError('GAME_MECH_RESOURCE_BOUND')
        return self
