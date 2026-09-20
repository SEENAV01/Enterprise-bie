from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import PurePosixPath
import json, math

class AudioCompilerError(ValueError):
    pass

@dataclass(frozen=True)
class AudioArtifact:
    artifact_id:str
    path:str
    content:str
    sha256:str
    required_dependencies:tuple[str,...]=()
    asset_paths:tuple[str,...]=()
    warnings:tuple[str,...]=()
    accepted:bool=False

def nonblank(value,name):
    if not isinstance(value,str) or not value.strip():
        raise AudioCompilerError(f"{name} required")
    return value.strip()

def nonnegative_int(value,name):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise AudioCompilerError(f"{name} must be nonnegative int")
    return value

def positive_int(value,name):
    value=nonnegative_int(value,name)
    if value<1:
        raise AudioCompilerError(f"{name} must be positive int")
    return value

def gain(value,name="volume"):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(float(value)):
        raise AudioCompilerError(f"{name} must be finite")
    value=float(value)
    if value<0 or value>1:
        raise AudioCompilerError(f"{name} must be in [0,1]")
    return value

def resolved_asset(value):
    value=nonblank(value,"resolved_asset_path")
    p=PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or "://" in value:
        raise AudioCompilerError("asset path must be public-relative and already resolved")
    return p.as_posix()

def js(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False)

def canonical_text(value):
    if not isinstance(value,str):
        raise AudioCompilerError("artifact content must be text")
    return value.replace("\r\n","\n").replace("\r","\n").rstrip("\n")+"\n"

def artifact(artifact_id,path,content,*,deps=(),assets=(),warnings=()):
    content=canonical_text(content)
    return AudioArtifact(
        nonblank(artifact_id,"artifact_id"),
        nonblank(path,"path"),
        content,
        sha256(content.encode("utf-8")).hexdigest(),
        tuple(sorted(set(deps))),
        tuple(sorted(set(assets))),
        tuple(sorted(set(warnings))),
        False,
    )
