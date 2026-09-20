from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
import json
class ContinuityError(ValueError):pass
@dataclass(frozen=True)
class VisualIdentity:
    entity_id:str;color_token:str|None=None;symbol_token:str|None=None;notation:str|None=None;coordinate_frame:str|None=None;representation:str|None=None;style_token:str|None=None
@dataclass(frozen=True)
class Transition:
    entity_id:str;field:str;old_value:str|None;new_value:str|None;scene_id:str;reason:str;evidence_refs:tuple[str,...]
@dataclass
class ContinuityLedger:
    identities:dict=field(default_factory=dict);transitions:list=field(default_factory=list);scenes:list=field(default_factory=list)
    def observe(self,scene_id,identity,evidence_refs=(),transition_reasons=None):
        if not scene_id or not identity.entity_id:raise ContinuityError("ids required")
        reasons=dict(transition_reasons or {});old=self.identities.get(identity.entity_id)
        if old:
            for field in ("color_token","symbol_token","notation","coordinate_frame","representation","style_token"):
                ov=getattr(old,field);nv=getattr(identity,field)
                if ov!=nv and ov is not None and nv is not None:
                    reason=reasons.get(field)
                    if not reason:raise ContinuityError(f"unjustified continuity change {identity.entity_id}.{field}")
                    if not evidence_refs:raise ContinuityError("transition requires evidence refs")
                    self.transitions.append(Transition(identity.entity_id,field,ov,nv,scene_id,reason,tuple(evidence_refs)))
        self.identities[identity.entity_id]=identity
        if scene_id not in self.scenes:self.scenes.append(scene_id)
        return identity
    def token_for(self,entity_id):
        if entity_id not in self.identities:raise ContinuityError("unknown entity")
        return self.identities[entity_id]
    def fingerprint(self):
        payload={"identities":{k:self.identities[k].__dict__ for k in sorted(self.identities)},
                 "transitions":[t.__dict__ for t in self.transitions],"scenes":self.scenes}
        return sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
