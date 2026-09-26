from __future__ import annotations
from dataclasses import fields,is_dataclass
from enum import Enum
from typing import get_args,get_origin,get_type_hints, Union
import json, types
from .canonical import canonical_json
from .errors import GameContractError
from . import expressions as ex
from .provenance import EvidenceRef,ProvenanceBundle
from .learning import LearningTarget
from .state import StateVariableSpec,StateModel
from .interaction import ActionSpec,EffectSpec,RuleSpec,InteractionContract,ActionKind,EffectKind
from .visual import VisualEntity,MotionCue,CameraCue,VisualExperienceContract,VisualKind,MotionKind,CameraKind
from .audio import AudioCue,AudioExperienceContract,AudioCueKind
from .feedback import FeedbackContract
from .adaptation import AdaptationRule,AdaptationContract,AdaptAction
from .quality_intent import ExperienceMode,ExperienceQualityIntent
from .document import ChallengeContract,GameLevelContract,GameExperienceContract,GameDocument

_TYPES={c.__name__:c for c in [EvidenceRef,ProvenanceBundle,LearningTarget,StateVariableSpec,StateModel,ActionSpec,EffectSpec,RuleSpec,InteractionContract,VisualEntity,MotionCue,CameraCue,VisualExperienceContract,AudioCue,AudioExperienceContract,FeedbackContract,AdaptationRule,AdaptationContract,ExperienceQualityIntent,ChallengeContract,GameLevelContract,GameExperienceContract,GameDocument,ex.Literal,ex.Variable,ex.Binary,ex.Compare,ex.Boolean,ex.Not]}
_ENUMS={c.__name__:c for c in [ex.ValueType,ex.BinaryOp,ex.CompareOp,ex.BoolOp,ActionKind,EffectKind,VisualKind,MotionKind,CameraKind,AudioCueKind,AdaptAction,ExperienceMode]}

def encode(value):
    if is_dataclass(value):return {'$type':type(value).__name__,**{f.name:encode(getattr(value,f.name)) for f in fields(value)}}
    if isinstance(value,Enum):return {'$enum':type(value).__name__,'value':value.value}
    if isinstance(value,tuple):return {'$tuple':[encode(x) for x in value]}
    if isinstance(value,list):return [encode(x) for x in value]
    if isinstance(value,dict):return {str(k):encode(v) for k,v in value.items()}
    if value is None or isinstance(value,(str,int,float,bool)):return value
    raise GameContractError('GAME_CODEC_ENCODE_TYPE',type(value).__name__)

def decode(value):
    if isinstance(value,list):return [decode(x) for x in value]
    if not isinstance(value,dict):return value
    if '$enum' in value:
        if set(value)!={'$enum','value'}:raise GameContractError('GAME_CODEC_ENUM_FIELDS')
        cls=_ENUMS.get(value['$enum'])
        if cls is None:raise GameContractError('GAME_CODEC_ENUM_UNKNOWN')
        try:return cls(value['value'])
        except ValueError as e:raise GameContractError('GAME_CODEC_ENUM_VALUE') from e
    if '$tuple' in value:
        if set(value)!={'$tuple'} or not isinstance(value['$tuple'],list):raise GameContractError('GAME_CODEC_TUPLE')
        return tuple(decode(x) for x in value['$tuple'])
    if '$type' in value:
        cls=_TYPES.get(value['$type'])
        if cls is None:raise GameContractError('GAME_CODEC_TYPE_UNKNOWN')
        expected={f.name for f in fields(cls)}|{'$type'}
        if set(value)!=expected:raise GameContractError('GAME_CODEC_FIELDS',value['$type'])
        kwargs={k:decode(v) for k,v in value.items() if k!='$type'}
        try:return cls(**kwargs)
        except TypeError as e:raise GameContractError('GAME_CODEC_CONSTRUCT',value['$type']) from e
    return {k:decode(v) for k,v in value.items()}

def dumps(value)->bytes:return canonical_json(encode(value))
def loads(data:bytes|str):
    try:raw=json.loads(data)
    except Exception as e:raise GameContractError('GAME_CODEC_JSON') from e
    return decode(raw)
