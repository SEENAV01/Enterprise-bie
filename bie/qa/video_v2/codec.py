"""Strict JSON: immutable typed request/policy; trust is supplied out of band."""
from dataclasses import fields,is_dataclass
from typing import get_type_hints,get_origin,get_args
from ..source_v2.codec import loads
from ..release_v2.contracts import ContractError
from .models import VideoRequest,VideoPolicy,ExecutionReceipt
from ..reasoning_v2.attestation import Review

def decode(value,cls,depth=0):
    if depth>48:raise ContractError('VIDEO_JSON_DEPTH')
    if get_origin(cls) is tuple:
        if type(value) is not list or len(value)>4096:raise ContractError('VIDEO_JSON_ARRAY')
        args=get_args(cls)
        if len(args)==2 and args[1] is Ellipsis:return tuple(decode(v,args[0],depth+1) for v in value)
        if len(value)!=len(args):raise ContractError('VIDEO_JSON_TUPLE')
        return tuple(decode(v,t,depth+1) for v,t in zip(value,args))
    if is_dataclass(cls):
        if type(value) is not dict or set(value)!={f.name for f in fields(cls)}:raise ContractError('VIDEO_JSON_FIELDS',cls.__name__)
        hints=get_type_hints(cls);return cls(**{k:decode(v,hints[k],depth+1) for k,v in value.items()})
    if cls in (str,int,bool):
        if type(value) is not cls:raise ContractError('VIDEO_JSON_TYPE')
        return value
    raise ContractError('VIDEO_JSON_UNSUPPORTED')

def load_request(data):return decode(loads(data),VideoRequest)
def load_policy(data):return decode(loads(data),VideoPolicy)
def load_receipt(data):return decode(loads(data),ExecutionReceipt)
def load_reviews(data):return decode(loads(data),tuple[Review,...])
