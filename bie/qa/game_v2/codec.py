"""Exact JSON field sets; no embedded trust keys or executable commands."""
from dataclasses import fields,is_dataclass
from typing import get_type_hints,get_origin,get_args
from ..source_v2.codec import loads
from ..release_v2.contracts import ContractError
from .models import GameRequest,GamePolicy,BuildReceipt,RuntimeReceipt

def decode(v,cls,depth=0):
    if depth>48:raise ContractError('GAME_JSON_DEPTH')
    if get_origin(cls) is tuple:
        if type(v) is not list or len(v)>4096:raise ContractError('GAME_JSON_ARRAY')
        args=get_args(cls)
        if len(args)==2 and args[1] is Ellipsis:return tuple(decode(x,args[0],depth+1) for x in v)
        if len(v)!=len(args):raise ContractError('GAME_JSON_TUPLE')
        return tuple(decode(x,t,depth+1) for x,t in zip(v,args))
    if is_dataclass(cls):
        if type(v) is not dict or set(v)!={f.name for f in fields(cls)}:raise ContractError('GAME_JSON_FIELDS',cls.__name__)
        hints=get_type_hints(cls);return cls(**{k:decode(x,hints[k],depth+1) for k,x in v.items()})
    if cls in (str,int,bool):
        if type(v) is not cls:raise ContractError('GAME_JSON_TYPE')
        return v
    raise ContractError('GAME_JSON_UNSUPPORTED')
def load_request(data):return decode(loads(data),GameRequest)
def load_policy(data):return decode(loads(data),GamePolicy)
def load_build(data):return decode(loads(data),BuildReceipt)
def load_runtime(data):return decode(loads(data),RuntimeReceipt)
