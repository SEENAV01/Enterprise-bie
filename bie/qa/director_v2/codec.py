"""Closed-world JSON; caller supplies policy/trust out of band."""
from dataclasses import fields,is_dataclass
from typing import get_type_hints,get_origin,get_args
from ..release_v2.contracts import ContractError
from ..source_v2.codec import loads
from .models import DirectorRequest,DirectorPolicy
from .attestation import Review

def decode(value,cls,depth=0):
    if depth>48:raise ContractError('DIR_JSON_DEPTH_LIMIT')
    if get_origin(cls) is tuple:
        if type(value) is not list or len(value)>4096:raise ContractError('INVALID_DIR_JSON_ARRAY')
        args=get_args(cls)
        if len(args)==2 and args[1] is Ellipsis:return tuple(decode(x,args[0],depth+1) for x in value)
        if len(value)!=len(args):raise ContractError('INVALID_DIR_JSON_TUPLE')
        return tuple(decode(x,t,depth+1) for x,t in zip(value,args))
    if is_dataclass(cls):
        if type(value) is not dict or set(value)!={f.name for f in fields(cls)}:raise ContractError('DIR_JSON_FIELDS_MISMATCH',cls.__name__)
        types=get_type_hints(cls);return cls(**{k:decode(v,types[k],depth+1) for k,v in value.items()})
    if cls in (str,int,bool):
        if type(value) is not cls:raise ContractError('DIR_JSON_TYPE_MISMATCH')
        return value
    raise ContractError('UNSUPPORTED_DIR_JSON_TYPE')
def request_from_dict(x):return decode(x,DirectorRequest)
def policy_from_dict(x):return decode(x,DirectorPolicy)
def load_request(data):return request_from_dict(loads(data))
def load_policy(data):return policy_from_dict(loads(data))
def load_reviews(data):return decode(loads(data),tuple[Review,...])
