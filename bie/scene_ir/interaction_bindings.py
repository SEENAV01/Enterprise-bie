from dataclasses import dataclass, field
from typing import Mapping, Any
from .interaction_common import *

@dataclass(frozen=True)
class InteractionBinding:
    binding_id:str
    interaction_id:str
    event_type:str
    target_ids:tuple[str,...]
    action:str
    handler_ref:str
    enabled_when:str|None=None
    payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        object.__setattr__(self,"binding_id",tok(self.binding_id,"binding_id"))
        object.__setattr__(self,"interaction_id",tok(self.interaction_id,"interaction_id"))
        if self.event_type not in {"tap","click","drag","hover","choice","scrub","keyboard","submit","simulation_control"}:
            raise InteractionIRError("unsupported event_type")
        object.__setattr__(self,"target_ids",unique_ids(self.target_ids,"target_ids"))
        object.__setattr__(self,"action",tok(self.action,"action"))
        object.__setattr__(self,"handler_ref",tok(self.handler_ref,"handler_ref"))
        if self.enabled_when is not None:
            object.__setattr__(self,"enabled_when",tok(self.enabled_when,"enabled_when"))
        object.__setattr__(self,"payload",dict(self.payload))

def validate_interaction_bindings(bindings, known_element_ids, known_handler_refs):
    bindings=tuple(bindings); elems=set(known_element_ids); handlers=set(known_handler_refs)
    if len({b.binding_id for b in bindings})!=len(bindings):
        raise InteractionIRError("duplicate binding_id")
    blockers=[]
    for b in bindings:
        for t in b.target_ids:
            if t not in elems:
                blockers.append("unknown_target:"+b.binding_id+":"+t)
        if b.handler_ref not in handlers:
            blockers.append("unknown_handler:"+b.binding_id)
    return tuple(sorted(set(blockers)))
