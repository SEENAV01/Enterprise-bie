from dataclasses import dataclass
from hashlib import sha256
import json
@dataclass(frozen=True)
class CompilerElement: element_id:str;element_type:str;props:dict;accessibility:dict
@dataclass(frozen=True)
class CompilerTrack: track_id:str;element_id:str;action:str;start_ms:int;end_ms:int;parameters:dict
@dataclass(frozen=True)
class CompilerPreflightHandoff:
    handoff_id:str;scene_id:str;scene_fingerprint:str;schema_version:str;target_profile:str
    elements:tuple[CompilerElement,...];tracks:tuple[CompilerTrack,...];resolved_asset_ids:tuple[str,...]
    capability_receipt:dict;provenance_receipt:dict;integrity_receipt:dict;accessibility_receipt:dict
    blockers:tuple[str,...];warnings:tuple[str,...];compiler_ready:bool
    compile_status:str="NOT_RUN";render_status:str="NOT_RUN";accepted:bool=False
def _hid(p): return "dsl-comp:"+sha256(json.dumps(p,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()[:24]
def build_compiler_preflight_handoff(document,*,target_profile,provenance_receipt,asset_receipt,integrity_receipt,accessibility_receipt,capability_receipt):
    blockers=[];warnings=[]
    for n,r in (("provenance",provenance_receipt),("assets",asset_receipt),("integrity",integrity_receipt),("accessibility",accessibility_receipt),("capability",capability_receipt)):
        if not getattr(r,"passed",False): blockers.append(n+"_not_ready")
        blockers.extend(n+":"+x for x in getattr(r,"blockers",()))
        warnings.extend(n+":"+x for x in getattr(r,"warnings",()))
    elems=tuple(CompilerElement(e.element_id,e.element_type,dict(e.props),dict(e.accessibility)) for e in document.elements)
    tracks=tuple(CompilerTrack(t.track_id,t.element_id,t.action,t.start_ms,t.end_ms,dict(t.parameters)) for t in document.tracks)
    payload={"scene_id":document.scene_id,"scene_fingerprint":document.fingerprint,"schema_version":document.schema_version,"target_profile":str(target_profile),"element_ids":[e.element_id for e in elems],"track_ids":[t.track_id for t in tracks],"asset_ids":list(getattr(asset_receipt,"resolved_assets",()))}
    return CompilerPreflightHandoff(_hid(payload),document.scene_id,document.fingerprint,document.schema_version,str(target_profile),elems,tracks,tuple(getattr(asset_receipt,"resolved_assets",())),{"passed":getattr(capability_receipt,"passed",False),"supported_requests":tuple(getattr(capability_receipt,"supported_requests",())),"fallback_ids":tuple(getattr(capability_receipt,"fallback_ids",()))},{"passed":getattr(provenance_receipt,"passed",False)},{"passed":getattr(integrity_receipt,"passed",False)},{"passed":getattr(accessibility_receipt,"passed",False),"reading_order":tuple(getattr(accessibility_receipt,"reading_order",())),"keyboard_focus_order":tuple(getattr(accessibility_receipt,"keyboard_focus_order",()))},tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),not blockers,"NOT_RUN","NOT_RUN",False)
def require_compiler_ready(h):
    if not h.compiler_ready: raise ValueError("not compiler-ready")
    if h.compile_status!="NOT_RUN" or h.render_status!="NOT_RUN": raise ValueError("preflight cannot claim execution")
    return True
