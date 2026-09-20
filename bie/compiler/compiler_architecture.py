from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

class CompilerArchitectureError(ValueError):
    pass

def _tok(value, name):
    if not isinstance(value, str) or not value.strip():
        raise CompilerArchitectureError(f"{name} must be nonblank")
    return value.strip()

@dataclass(frozen=True)
class CompilerTargetProfile:
    profile_id:str
    width:int
    height:int
    fps:int
    pixel_format:str="yuv420p"

    def __post_init__(self):
        object.__setattr__(self, "profile_id", _tok(self.profile_id, "profile_id"))
        for name in ("width","height","fps"):
            value=getattr(self,name)
            if isinstance(value,bool) or not isinstance(value,int) or value<1:
                raise CompilerArchitectureError(f"{name} must be positive int")
        object.__setattr__(self, "pixel_format", _tok(self.pixel_format, "pixel_format"))

@dataclass(frozen=True)
class CompilerStage:
    stage_id:str
    depends_on:tuple[str,...]
    produces:str

    def __post_init__(self):
        object.__setattr__(self,"stage_id",_tok(self.stage_id,"stage_id"))
        object.__setattr__(self,"depends_on",tuple(_tok(x,"depends_on") for x in self.depends_on))
        object.__setattr__(self,"produces",_tok(self.produces,"produces"))

@dataclass(frozen=True)
class CompilerRequest:
    request_id:str
    scene_id:str
    scene_fingerprint:str
    target:CompilerTargetProfile
    compiler_version:str
    deterministic_seed:int=0
    output_kind:str="remotion_project"

    def __post_init__(self):
        for name in ("request_id","scene_id","scene_fingerprint","compiler_version","output_kind"):
            object.__setattr__(self,name,_tok(getattr(self,name),name))
        if len(self.scene_fingerprint)!=64 or any(c not in "0123456789abcdef" for c in self.scene_fingerprint):
            raise CompilerArchitectureError("scene_fingerprint must be sha256 hex")
        if isinstance(self.deterministic_seed,bool) or not isinstance(self.deterministic_seed,int):
            raise CompilerArchitectureError("deterministic_seed must be int")

@dataclass(frozen=True)
class CompilerPlan:
    plan_id:str
    request:CompilerRequest
    stages:tuple[CompilerStage,...]
    build_status:str="NOT_RUN"
    render_status:str="NOT_RUN"
    accepted:bool=False

def canonical_compiler_stages():
    return (
        CompilerStage("scene_ir_load",(), "loaded_scene_ir"),
        CompilerStage("capability_resolution",("scene_ir_load",), "capability_plan"),
        CompilerStage("component_resolution",("capability_resolution",), "component_plan"),
        CompilerStage("codegen",("component_resolution",), "source_tree"),
        CompilerStage("build",("codegen",), "build_artifacts"),
        CompilerStage("render",("build",), "render_artifacts"),
    )

def validate_stage_graph(stages):
    stages=tuple(stages)
    ids=[s.stage_id for s in stages]
    if len(ids)!=len(set(ids)):
        raise CompilerArchitectureError("duplicate stage_id")
    seen=set()
    for s in stages:
        missing=set(s.depends_on)-seen
        if missing:
            raise CompilerArchitectureError(f"stage {s.stage_id} depends on unavailable {sorted(missing)}")
        seen.add(s.stage_id)
    return True

def make_compiler_plan(request, stages=None):
    stages=tuple(stages or canonical_compiler_stages())
    validate_stage_graph(stages)
    payload={
        "request_id":request.request_id,
        "scene_id":request.scene_id,
        "scene_fingerprint":request.scene_fingerprint,
        "target":request.target.__dict__,
        "compiler_version":request.compiler_version,
        "seed":request.deterministic_seed,
        "output_kind":request.output_kind,
        "stages":[s.__dict__ for s in stages],
    }
    raw=json.dumps(payload,sort_keys=True,separators=(",",":"))
    plan_id="comp-plan:"+sha256(raw.encode()).hexdigest()[:24]
    return CompilerPlan(plan_id,request,stages,"NOT_RUN","NOT_RUN",False)
