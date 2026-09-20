from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json

class DeterministicCodegenError(ValueError):
    pass

@dataclass(frozen=True)
class SourceFile:
    path:str
    content:str
    sha256:str

@dataclass(frozen=True)
class CodegenPlan:
    scene_fingerprint:str
    compiler_version:str
    deterministic_seed:int
    component_snapshot:tuple
    files:tuple[SourceFile,...]
    manifest_sha256:str
    accepted:bool=False

def _safe_rel(path):
    p=Path(path)
    if p.is_absolute() or ".." in p.parts or not p.parts:
        raise DeterministicCodegenError("unsafe generated path")
    return p.as_posix()

def _normalize_content(content):
    if not isinstance(content,str):
        raise DeterministicCodegenError("generated content must be text")
    return content.replace("\r\n","\n").replace("\r","\n").rstrip("\n")+"\n"

def plan_deterministic_codegen(*,scene_fingerprint,compiler_version,deterministic_seed,component_snapshot,files):
    if len(scene_fingerprint)!=64 or any(c not in "0123456789abcdef" for c in scene_fingerprint):
        raise DeterministicCodegenError("scene_fingerprint invalid")
    if not isinstance(compiler_version,str) or not compiler_version.strip():
        raise DeterministicCodegenError("compiler_version required")
    if isinstance(deterministic_seed,bool) or not isinstance(deterministic_seed,int):
        raise DeterministicCodegenError("deterministic_seed must be int")

    normalized=[]
    seen=set()
    for path,content in files:
        path=_safe_rel(path)
        if path in seen:
            raise DeterministicCodegenError("duplicate generated path")
        seen.add(path)
        content=_normalize_content(content)
        digest=sha256(content.encode("utf-8")).hexdigest()
        normalized.append(SourceFile(path,content,digest))
    normalized.sort(key=lambda f:f.path)

    payload={
        "scene_fingerprint":scene_fingerprint,
        "compiler_version":compiler_version.strip(),
        "deterministic_seed":deterministic_seed,
        "component_snapshot":list(component_snapshot),
        "files":[{"path":f.path,"sha256":f.sha256} for f in normalized],
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"),default=list)
    manifest=sha256(raw.encode("utf-8")).hexdigest()
    return CodegenPlan(
        scene_fingerprint,compiler_version.strip(),deterministic_seed,
        tuple(component_snapshot),tuple(normalized),manifest,False
    )

def write_codegen_plan(plan, root):
    root=Path(root).resolve()
    root.mkdir(parents=True,exist_ok=True)
    written=[]
    for source in plan.files:
        target=(root/source.path).resolve()
        try:
            target.relative_to(root)
        except Exception as exc:
            raise DeterministicCodegenError("generated file escapes output root") from exc
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(source.content,encoding="utf-8",newline="\n")
        if sha256(target.read_bytes()).hexdigest()!=source.sha256:
            raise DeterministicCodegenError("written file hash mismatch")
        written.append(target.relative_to(root).as_posix())
    manifest_path=root/"CODEGEN_MANIFEST.json"
    manifest_path.write_text(
        json.dumps({
            "scene_fingerprint":plan.scene_fingerprint,
            "compiler_version":plan.compiler_version,
            "deterministic_seed":plan.deterministic_seed,
            "manifest_sha256":plan.manifest_sha256,
            "files":[{"path":f.path,"sha256":f.sha256} for f in plan.files],
            "accepted":False,
        },sort_keys=True,indent=2)+"\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(written)
