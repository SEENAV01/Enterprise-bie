from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping
import json, re

class ElementCompilerError(ValueError):
    pass

@dataclass(frozen=True)
class ElementCompileResult:
    element_id:str
    element_type:str
    component_name:str
    source_path:str
    source_text:str
    source_sha256:str
    required_dependencies:tuple[str,...]=()
    asset_paths:tuple[str,...]=()
    warnings:tuple[str,...]=()
    accepted:bool=False

def _get(obj,name,default=None):
    if isinstance(obj,dict):
        return obj.get(name,default)
    return getattr(obj,name,default)

def normalize_element(element):
    eid=_get(element,"element_id")
    etype=_get(element,"element_type")
    props=_get(element,"props",{}) or {}
    acc=_get(element,"accessibility",{}) or {}
    src=tuple(_get(element,"source_refs",()) or ())
    rsn=tuple(_get(element,"reasoning_refs",()) or ())
    if not isinstance(eid,str) or not eid.strip():
        raise ElementCompilerError("element_id required")
    if not isinstance(etype,str) or not etype.strip():
        raise ElementCompilerError("element_type required")
    if not isinstance(props,Mapping):
        raise ElementCompilerError("props must be mapping")
    if not isinstance(acc,Mapping):
        raise ElementCompilerError("accessibility must be mapping")
    if not src or not rsn:
        raise ElementCompilerError("source/reasoning lineage required")
    return eid.strip(),etype.strip(),dict(props),dict(acc),src,rsn

def require_type(element,expected):
    eid,etype,props,acc,src,rsn=normalize_element(element)
    if etype!=expected:
        raise ElementCompilerError(f"expected {expected}, got {etype}")
    return eid,props,acc,src,rsn

def component_name(prefix,element_id):
    clean=re.sub(r"[^A-Za-z0-9_$]","_",element_id)
    if not clean or not re.match(r"^[A-Za-z_$]",clean):
        clean="E_"+clean
    suffix=sha256(element_id.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{clean}_{suffix}"

def jsx(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True)

def canonical_text(value):
    if not isinstance(value,str):
        raise ElementCompilerError("generated source must be text")
    return value.replace("\r\n","\n").replace("\r","\n").rstrip("\n")+"\n"

def compile_result(element_id,element_type,component,source,*,dependencies=(),assets=(),warnings=()):
    source=canonical_text(source)
    path=f"src/elements/{component}.tsx"
    return ElementCompileResult(
        element_id,element_type,component,path,source,
        sha256(source.encode("utf-8")).hexdigest(),
        tuple(sorted(set(dependencies))),tuple(sorted(set(assets))),
        tuple(sorted(set(warnings))),False
    )

def require_resolved_asset(props,key="resolved_asset_path"):
    value=props.get(key)
    if not isinstance(value,str) or not value.strip():
        raise ElementCompilerError(f"{key} required; unresolved asset_ref must not reach generated source")
    value=value.strip()
    if value.startswith("/") or ".." in value.split("/") or "://" in value:
        raise ElementCompilerError(f"{key} must be public-relative path")
    return value
