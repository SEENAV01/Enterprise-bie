from __future__ import annotations
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Mapping, Any, Sequence
import json

class CapabilityHandoffError(ValueError): pass

@dataclass(frozen=True)
class PrimitiveRequirement:
    primitive_id:str
    primitive_type:str
    required:bool=True
    capability_tags:tuple[str,...]=()
    fallback_type:str|None=None
    source_refs:tuple[str,...]=()
    reasoning_refs:tuple[str,...]=()

@dataclass(frozen=True)
class AssetBinding:
    asset_id:str
    uri:str
    content_sha256:str
    rights_status:str
    source_refs:tuple[str,...]

@dataclass(frozen=True)
class TimingBinding:
    visual_id:str
    start_ms:int
    end_ms:int
    focus:bool=False
    reveal:bool=False
    narration_revision:int=1

@dataclass(frozen=True)
class DownstreamVisualHandoff:
    handoff_id:str
    plan_fingerprint:str
    primitives:tuple[PrimitiveRequirement,...]
    assets:tuple[AssetBinding,...]
    timing:tuple[TimingBinding,...]
    accessibility_ready:bool
    required_2d:bool
    required_3d:bool
    unsupported_capabilities:tuple[str,...]
    planned_fallbacks:Mapping[str,str]
    target_profile:str
    handoff_fingerprint:str
    review_required:bool=True
    accepted:bool=False

def _fp(payload):
    return sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def build_downstream_handoff(*,handoff_id,plan_fingerprint,primitives:Sequence[PrimitiveRequirement],
                             assets:Sequence[AssetBinding],timing:Sequence[TimingBinding],
                             accessibility_ready,target_capabilities,target_profile):
    if not handoff_id or len(plan_fingerprint)!=64 or not target_profile:
        raise CapabilityHandoffError("invalid handoff identity")
    caps=set(target_capabilities); unsupported=[]; fallbacks={}
    for p in primitives:
        if not p.primitive_id or not p.primitive_type or not p.source_refs or not p.reasoning_refs:
            raise CapabilityHandoffError("primitive missing lineage")
        missing=sorted(set(p.capability_tags)-caps)
        if missing:
            if p.fallback_type:
                fallbacks[p.primitive_id]=p.fallback_type
            elif p.required:
                unsupported.extend(f"{p.primitive_id}:{m}" for m in missing)
    for a in assets:
        if not a.uri or len(a.content_sha256)!=64 or a.rights_status not in {"owned","public_domain","licensed","source-permitted"} or not a.source_refs:
            raise CapabilityHandoffError("asset not handoff-ready")
    for t in timing:
        if t.start_ms<0 or t.end_ms<=t.start_ms or t.narration_revision<1:
            raise CapabilityHandoffError("invalid timing binding")
    if not accessibility_ready:
        unsupported.append("accessibility:not_ready")
    required_3d=any("3d" in p.capability_tags for p in primitives)
    required_2d=any("2d" in p.capability_tags or "3d" not in p.capability_tags for p in primitives)
    payload={"handoff_id":handoff_id,"plan_fingerprint":plan_fingerprint,
             "primitives":[p.__dict__ for p in primitives],"assets":[a.__dict__ for a in assets],
             "timing":[t.__dict__ for t in timing],"accessibility_ready":bool(accessibility_ready),
             "required_2d":required_2d,"required_3d":required_3d,
             "unsupported":sorted(set(unsupported)),"fallbacks":dict(sorted(fallbacks.items())),
             "target_profile":target_profile}
    return DownstreamVisualHandoff(handoff_id,plan_fingerprint,tuple(primitives),tuple(assets),tuple(timing),
                                   bool(accessibility_ready),required_2d,required_3d,tuple(sorted(set(unsupported))),
                                   dict(sorted(fallbacks.items())),target_profile,_fp(payload),True,False)

def assert_handoff_consumable(handoff):
    if handoff.unsupported_capabilities:
        raise CapabilityHandoffError("unsupported capabilities remain unresolved")
    return True
