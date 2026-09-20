from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json, re

class AnimationCompilerError(ValueError):
    pass

@dataclass(frozen=True)
class AnimationCompileResult:
    track_id:str
    action:str
    source_path:str
    source_text:str
    source_sha256:str
    warnings:tuple[str,...]=()
    accepted:bool=False

def _get(obj,name,default=None):
    if isinstance(obj,dict):
        return obj.get(name,default)
    return getattr(obj,name,default)

def normalize_track(track):
    track_id=_get(track,"track_id")
    element_id=_get(track,"element_id")
    action=_get(track,"action")
    start_ms=_get(track,"start_ms")
    end_ms=_get(track,"end_ms")
    params=_get(track,"parameters",{}) or {}
    src=tuple(_get(track,"source_refs",()) or ())
    rsn=tuple(_get(track,"reasoning_refs",()) or ())
    for name,value in (("track_id",track_id),("element_id",element_id),("action",action)):
        if not isinstance(value,str) or not value.strip():
            raise AnimationCompilerError(f"{name} required")
    if isinstance(start_ms,bool) or not isinstance(start_ms,int) or start_ms<0:
        raise AnimationCompilerError("start_ms invalid")
    if isinstance(end_ms,bool) or not isinstance(end_ms,int) or end_ms<=start_ms:
        raise AnimationCompilerError("end_ms invalid")
    if not isinstance(params,dict):
        params=dict(params)
    if not src or not rsn:
        raise AnimationCompilerError("track source/reasoning lineage required")
    return track_id.strip(),element_id.strip(),action.strip(),start_ms,end_ms,dict(params),src,rsn

def component_name(prefix,track_id):
    clean=re.sub(r"[^A-Za-z0-9_$]","_",track_id)
    if not clean or not re.match(r"^[A-Za-z_$]",clean):
        clean="T_"+clean
    suffix=sha256(track_id.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{clean}_{suffix}"

def jsx(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False)

def canonical_text(value):
    if not isinstance(value,str):
        raise AnimationCompilerError("generated source must be text")
    return value.replace("\r\n","\n").replace("\r","\n").rstrip("\n")+"\n"

def compile_result(track_id,action,path,source,warnings=()):
    source=canonical_text(source)
    return AnimationCompileResult(
        track_id,action,path,source,sha256(source.encode("utf-8")).hexdigest(),
        tuple(sorted(set(warnings))),False
    )

def ms_to_frame_expr(ms):
    if isinstance(ms,bool) or not isinstance(ms,int) or ms<0:
        raise AnimationCompilerError("ms must be nonnegative int")
    return f"Math.round(({ms} / 1000) * fps)"
