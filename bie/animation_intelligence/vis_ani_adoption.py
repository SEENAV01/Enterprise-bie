from dataclasses import dataclass
class VisAdoptionError(ValueError):pass
class StaleVisualHandoffError(VisAdoptionError):pass
@dataclass(frozen=True)
class AdoptedVisualHandoff:
    handoff_id:str;plan_fingerprint:str;visual_revision:int;target_profile:str;primitives:tuple;timing:tuple;fallbacks:dict;accepted:bool=False
def adopt_visual_handoff(d,visual_revision,expected_plan_fingerprint=None):
    for k in ("handoff_id","plan_fingerprint","primitives","timing","accessibility_ready","target_profile"):
        if k not in d:raise VisAdoptionError("missing "+k)
    if d.get("current") is False or d.get("invalidated_by"):raise StaleVisualHandoffError("stale VIS handoff")
    if expected_plan_fingerprint and d["plan_fingerprint"]!=expected_plan_fingerprint:raise StaleVisualHandoffError("VIS fingerprint mismatch")
    if len(d["plan_fingerprint"])!=64 or visual_revision<1:raise VisAdoptionError("invalid fingerprint/revision")
    if not d["accessibility_ready"]:raise VisAdoptionError("accessibility not ready")
    fb=dict(d.get("planned_fallbacks",{}))
    for item in d.get("unsupported_capabilities",()):
        if str(item).split(":",1)[0] not in fb:raise VisAdoptionError("unresolved capability")
    for p in d["primitives"]:
        if not p.get("primitive_id") or not p.get("source_refs") or not p.get("reasoning_refs"):raise VisAdoptionError("primitive lineage missing")
    return AdoptedVisualHandoff(d["handoff_id"],d["plan_fingerprint"],visual_revision,d["target_profile"],tuple(d["primitives"]),tuple(d["timing"]),fb,False)
