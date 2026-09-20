from dataclasses import dataclass
from .unsupported_capability_failure import CapabilityRequest
from .planned_fallback_contract import PlannedFallback,validate_fallback
@dataclass(frozen=True)
class CapabilityResolutionReceipt:
    scene_id:str;target_profile:str;supported_requests:tuple[str,...];fallback_ids:tuple[str,...];blockers:tuple[str,...];warnings:tuple[str,...];passed:bool;accepted:bool=False
def resolve_compiler_capabilities(document,registry,target_profile):
    target_profile=str(target_profile);requests=[dict(x) for x in document.capability_requests];fallbacks=[dict(x) for x in document.planned_fallbacks]
    fb_by={(x.get("element_id"),x.get("missing_capability_id")):x for x in fallbacks};blockers=[];warnings=[];supported=[];used=[];types={e.element_id:e.element_type for e in document.elements}
    for raw in requests:
        try:req=CapabilityRequest(raw["capability_id"],raw["element_id"],raw.get("element_type") or types.get(raw["element_id"]),raw["requested_action"],target_profile,raw.get("reason_code","scene_ir_request"),bool(raw.get("required",True)))
        except Exception:
            blockers.append("malformed_capability_request:"+str(raw.get("capability_id","?")));continue
        if req.element_id not in types:blockers.append("capability_request_unknown_element:"+req.element_id);continue
        if registry.supports(req.capability_id,req.element_type,req.requested_action,target_profile):
            supported.append(req.capability_id+":"+req.element_id+":"+req.requested_action);continue
        rawfb=fb_by.get((req.element_id,req.capability_id))
        if rawfb is None:
            msg="unsupported_capability_no_fallback:"+req.capability_id+":"+req.element_id
            (blockers if req.required else warnings).append(msg);continue
        try:
            fb=PlannedFallback(rawfb["fallback_id"],rawfb["element_id"],rawfb["missing_capability_id"],rawfb["fallback_capability_id"],rawfb["fallback_action"],rawfb["semantic_equivalence"],bool(rawfb["preserves_source_refs"]),bool(rawfb["preserves_reasoning_refs"]),bool(rawfb["preserves_accessibility"]),bool(rawfb.get("required_review",True)))
            b,w=validate_fallback(fb,registry,target_profile,req.element_type)
        except Exception:
            blockers.append("malformed_fallback:"+str(rawfb.get("fallback_id","?")));continue
        if b:blockers.extend("fallback_invalid:"+fb.fallback_id+":"+x for x in b)
        else:
            used.append(fb.fallback_id);warnings.extend("fallback_warning:"+fb.fallback_id+":"+x for x in w)
    return CapabilityResolutionReceipt(document.scene_id,target_profile,tuple(sorted(supported)),tuple(sorted(used)),tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,False)
