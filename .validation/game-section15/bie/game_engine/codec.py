from __future__ import annotations
from dataclasses import fields,is_dataclass
from enum import Enum
from typing import get_args,get_origin,get_type_hints, Union
import json, types, math
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

def _decode(value):
    if isinstance(value,list):return [_decode(x) for x in value]
    if not isinstance(value,dict):return value
    if '$enum' in value:
        if set(value)!={'$enum','value'}:raise GameContractError('GAME_CODEC_ENUM_FIELDS')
        if type(value['$enum']) is not str:raise GameContractError('GAME_CODEC_ENUM_UNKNOWN')
        cls=_ENUMS.get(value['$enum'])
        if cls is None:raise GameContractError('GAME_CODEC_ENUM_UNKNOWN')
        try:return cls(value['value'])
        except (ValueError,TypeError) as e:raise GameContractError('GAME_CODEC_ENUM_VALUE') from e
    if '$tuple' in value:
        if set(value)!={'$tuple'} or not isinstance(value['$tuple'],list):raise GameContractError('GAME_CODEC_TUPLE')
        return tuple(_decode(x) for x in value['$tuple'])
    if '$type' in value:
        if type(value['$type']) is not str:raise GameContractError('GAME_CODEC_TYPE_UNKNOWN')
        cls=_TYPES.get(value['$type'])
        if cls is None:raise GameContractError('GAME_CODEC_TYPE_UNKNOWN')
        expected={f.name for f in fields(cls)}|{'$type'}
        if set(value)!=expected:raise GameContractError('GAME_CODEC_FIELDS',value['$type'])
        kwargs={k:_decode(v) for k,v in value.items() if k!='$type'}
        try:return cls(**kwargs)
        except TypeError as e:raise GameContractError('GAME_CODEC_CONSTRUCT',value['$type']) from e
    return {k:_decode(v) for k,v in value.items()}

MAX_WIRE_BYTES=2_000_000
MAX_JSON_DEPTH=128
MAX_JSON_NODES=100_000

def _bounded(value,depth=0,budget=None):
    budget=[MAX_JSON_NODES] if budget is None else budget
    budget[0]-=1
    if depth>MAX_JSON_DEPTH or budget[0]<0:raise GameContractError('GAME_CODEC_COMPLEXITY_LIMIT')
    if type(value) is dict:
        for key,child in value.items():
            if type(key) is not str:raise GameContractError('GAME_CODEC_KEY_TYPE')
            _bounded(key,depth+1,budget);_bounded(child,depth+1,budget)
    elif type(value) is list:
        for child in value:_bounded(child,depth+1,budget)
    elif type(value) is str:
        try:value.encode('utf-8')
        except UnicodeError as exc:raise GameContractError('GAME_CODEC_UNICODE') from exc
    elif type(value) is float:
        if not math.isfinite(value):raise GameContractError('GAME_CODEC_NONFINITE')
    elif value is not None and type(value) not in (int,bool):raise GameContractError('GAME_CODEC_JSON_TYPE')

def decode(value):
    _bounded(value)
    return _decode(value)

def _pairs(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise GameContractError('GAME_CODEC_DUPLICATE_JSON_KEY')
        out[key]=value
    return out

def dumps(value)->bytes:return canonical_json(encode(value))
def loads(data:bytes|str):
    if type(data) not in (bytes,str):raise GameContractError('GAME_CODEC_WIRE_TYPE')
    try:wire=data.encode('utf-8') if type(data) is str else data
    except UnicodeError as e:raise GameContractError('GAME_CODEC_UNICODE') from e
    if len(wire)>MAX_WIRE_BYTES:raise GameContractError('GAME_CODEC_WIRE_LIMIT')
    try:raw=json.loads(wire,object_pairs_hook=_pairs)
    except GameContractError:raise
    except (ValueError,UnicodeError,RecursionError) as e:raise GameContractError('GAME_CODEC_JSON') from e
    return decode(raw)
