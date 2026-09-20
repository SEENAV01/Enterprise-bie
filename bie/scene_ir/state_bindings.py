from dataclasses import dataclass, field
from typing import Mapping, Any
from .interaction_common import *

@dataclass(frozen=True)
class StateBinding:
    binding_id:str
    state_path:str
    target_id:str
    property_name:str
    transform:str="identity"
    default_value:Any=None
    read_only:bool=False
    def __post_init__(self):
        object.__setattr__(self,"binding_id",tok(self.binding_id,"binding_id"))
        object.__setattr__(self,"state_path",tok(self.state_path,"state_path"))
        object.__setattr__(self,"target_id",tok(self.target_id,"target_id"))
        object.__setattr__(self,"property_name",tok(self.property_name,"property_name"))
        if self.transform not in {"identity","bool","number","string","percent","clamp01","lookup","format"}:
            raise InteractionIRError("unsupported transform")

def validate_state_bindings(bindings, known_state_paths, known_element_ids):
    bindings=tuple(bindings); states=set(known_state_paths); elems=set(known_element_ids)
    if len({b.binding_id for b in bindings})!=len(bindings):
        raise InteractionIRError("duplicate binding_id")
    blockers=[]
    for b in bindings:
        if b.state_path not in states:
            blockers.append("unknown_state_path:"+b.binding_id)
        if b.target_id not in elems:
            blockers.append("unknown_target:"+b.binding_id)
    return tuple(sorted(set(blockers)))

def apply_state_transform(binding, value, lookup=None):
    t=binding.transform
    if t=="identity": return value
    if t=="bool": return bool(value)
    if t=="number": return float(value)
    if t=="string": return str(value)
    if t=="percent": return f"{float(value)*100:.0f}%"
    if t=="clamp01": return max(0.0,min(1.0,float(value)))
    if t=="lookup":
        if lookup is None or value not in lookup:
            raise InteractionIRError("lookup transform missing key")
        return lookup[value]
    if t=="format":
        return str(binding.default_value).format(value)
    raise InteractionIRError("unsupported transform")
