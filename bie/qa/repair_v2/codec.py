"""Closed-world typed data; no executable paths, callables or keys in wire data."""
from dataclasses import fields,is_dataclass
from typing import get_type_hints,get_origin,get_args
from ..source_v2.codec import loads
from ..release_v2.contracts import ContractError
from .models import Snapshot,FailureBatch,RepairPolicy,Proposal,CheckOutcome

def decode(v,cls,depth=0):
    if depth>40:raise ContractError('REPAIR_JSON_DEPTH')
    if get_origin(cls) is tuple:
        if type(v) is not list or len(v)>4096:raise ContractError('REPAIR_JSON_ARRAY')
        args=get_args(cls)
        if len(args)==2 and args[1] is Ellipsis:return tuple(decode(x,args[0],depth+1) for x in v)
        if len(v)!=len(args):raise ContractError('REPAIR_JSON_TUPLE')
        return tuple(decode(x,t,depth+1) for x,t in zip(v,args))
    if is_dataclass(cls):
        if type(v) is not dict or set(v)!={f.name for f in fields(cls)}:raise ContractError('REPAIR_JSON_FIELDS',cls.__name__)
        hints=get_type_hints(cls);return cls(**{k:decode(x,hints[k],depth+1) for k,x in v.items()})
    if cls in (str,int,bool):
        if type(v) is not cls:raise ContractError('REPAIR_JSON_TYPE')
        return v
    raise ContractError('REPAIR_JSON_UNSUPPORTED')

def load_snapshot(b):return decode(loads(b),Snapshot)
def load_batch(b):return decode(loads(b),FailureBatch)
def load_policy(b):return decode(loads(b),RepairPolicy)
def load_proposal(b):return decode(loads(b),Proposal)
def load_outcome(b):return decode(loads(b),CheckOutcome)
