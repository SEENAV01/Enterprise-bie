from __future__ import annotations
from dataclasses import dataclass,field
from hashlib import sha256
from math import isfinite
from typing import Any,Mapping
import json,re

class VisualPlanError(ValueError): pass
class VisualPlanVersionError(VisualPlanError): pass
class VisualPlanStageError(VisualPlanError): pass
class VisualPlanCurrentnessError(VisualPlanError): pass
STAGES=("DIR_ADOPT","REP","GRAM","LAYOUT","ASSET","TEXT","ACCESS","QA")
SEMVER=re.compile(r"^\d+\.\d+\.\d+$")
HEX64=re.compile(r"^[0-9a-f]{64}$")

def token(v,n):
    if not isinstance(v,str) or not v.strip(): raise VisualPlanError(f"{n} blank")
    return v.strip()
def ids(v,n,empty=False):
    out=tuple(token(x,n) for x in (v or ()))
    if not empty and not out: raise VisualPlanError(f"{n} empty")
    if len(set(out))!=len(out): raise VisualPlanError(f"{n} duplicate")
    return out
def canon(v):
    if isinstance(v,Mapping): return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if isinstance(v,set): return sorted(canon(x) for x in v)
    if isinstance(v,float):
        if not isfinite(v): raise VisualPlanError("nonfinite")
        return v
    if v is None or isinstance(v,(str,int,bool)): return v
    raise VisualPlanError(type(v).__name__)
def fp(v): return sha256(json.dumps(canon(v),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def semver(v,n):
    v=token(v,n)
    if not SEMVER.fullmatch(v): raise VisualPlanVersionError(f"{n} invalid semver")
    return v
def revision(v,n):
    if isinstance(v,bool) or not isinstance(v,int) or v<1: raise VisualPlanError(f"{n} invalid")
    return v

@dataclass(frozen=True)
class StageRef:
    stage:str; artifact_id:str; revision:int; artifact_fingerprint:str
    evidence_refs:tuple[str,...]; reasoning_refs:tuple[str,...]
    current:bool=True; status:str="PASS"; payload:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        st=token(self.stage,"stage").upper()
        if st not in STAGES: raise VisualPlanStageError(st)
        object.__setattr__(self,"stage",st)
        object.__setattr__(self,"artifact_id",token(self.artifact_id,"artifact_id"))
        object.__setattr__(self,"revision",revision(self.revision,"revision"))
        f=token(self.artifact_fingerprint,"artifact_fingerprint").lower()
        if not HEX64.fullmatch(f): raise VisualPlanError("bad sha256")
        object.__setattr__(self,"artifact_fingerprint",f)
        object.__setattr__(self,"evidence_refs",ids(self.evidence_refs,"evidence_refs"))
        object.__setattr__(self,"reasoning_refs",ids(self.reasoning_refs,"reasoning_refs"))
        s=token(self.status,"status").upper()
        if s not in {"PASS","REVIEW","BLOCKED","UNSUPPORTED"}: raise VisualPlanStageError("bad status")
        object.__setattr__(self,"status",s)
        object.__setattr__(self,"payload",canon(dict(self.payload)))
    def data(self):
        return {"stage":self.stage,"artifact_id":self.artifact_id,"revision":self.revision,
                "artifact_fingerprint":self.artifact_fingerprint,"evidence_refs":self.evidence_refs,
                "reasoning_refs":self.reasoning_refs,"current":self.current,"status":self.status,"payload":self.payload}

@dataclass(frozen=True)
class VisualPlan:
    plan_id:str; schema_version:str; policy_version:str
    source_id:str; source_revision:int; dir_id:str; dir_revision:int; target_profile:str
    stages:tuple[StageRef,...]; current:bool; review_required:bool=True; accepted:bool=False; fingerprint:str=""
    def __post_init__(self):
        object.__setattr__(self,"plan_id",token(self.plan_id,"plan_id"))
        object.__setattr__(self,"schema_version",semver(self.schema_version,"schema"))
        object.__setattr__(self,"policy_version",semver(self.policy_version,"policy"))
        object.__setattr__(self,"source_id",token(self.source_id,"source_id"))
        object.__setattr__(self,"source_revision",revision(self.source_revision,"source_revision"))
        object.__setattr__(self,"dir_id",token(self.dir_id,"dir_id"))
        object.__setattr__(self,"dir_revision",revision(self.dir_revision,"dir_revision"))
        object.__setattr__(self,"target_profile",token(self.target_profile,"target_profile"))
        if self.accepted: raise VisualPlanError("cannot self-accept")
        names=tuple(x.stage for x in self.stages)
        if names!=STAGES[:len(names)]: raise VisualPlanStageError("stages must be canonical prefix")
        calc=self.compute()
        if self.fingerprint and self.fingerprint!=calc: raise VisualPlanError("fingerprint mismatch")
        object.__setattr__(self,"fingerprint",calc)
    def compute(self):
        return fp({"plan_id":self.plan_id,"schema_version":self.schema_version,"policy_version":self.policy_version,
                   "source_id":self.source_id,"source_revision":self.source_revision,"dir_id":self.dir_id,
                   "dir_revision":self.dir_revision,"target_profile":self.target_profile,
                   "stages":[s.data() for s in self.stages],"current":self.current,"accepted":False})
    def to_dict(self):
        return {"plan_id":self.plan_id,"schema_version":self.schema_version,"policy_version":self.policy_version,
                "source_id":self.source_id,"source_revision":self.source_revision,"dir_id":self.dir_id,
                "dir_revision":self.dir_revision,"target_profile":self.target_profile,
                "stages":[s.data() for s in self.stages],"current":self.current,"review_required":self.review_required,
                "accepted":False,"fingerprint":self.fingerprint}
    @classmethod
    def from_dict(cls,d):
        return cls(d["plan_id"],d["schema_version"],d["policy_version"],d["source_id"],d["source_revision"],
                   d["dir_id"],d["dir_revision"],d["target_profile"],tuple(StageRef(**x) for x in d["stages"]),
                   d["current"],d.get("review_required",True),d.get("accepted",False),d.get("fingerprint",""))

def build_plan(plan_id,schema_version,policy_version,source_id,source_revision,dir_id,dir_revision,target_profile,stages):
    stages=tuple(stages)
    current=all(s.current and s.status in {"PASS","REVIEW"} for s in stages)
    return VisualPlan(plan_id,schema_version,policy_version,source_id,source_revision,dir_id,dir_revision,target_profile,stages,current)
def append_stage(plan,ref):
    if not plan.current: raise VisualPlanCurrentnessError("stale plan")
    if len(plan.stages)>=len(STAGES) or ref.stage!=STAGES[len(plan.stages)]: raise VisualPlanStageError("wrong next stage")
    return build_plan(plan.plan_id,plan.schema_version,plan.policy_version,plan.source_id,plan.source_revision,plan.dir_id,plan.dir_revision,plan.target_profile,plan.stages+(ref,))
def assert_compatible(plan,schema_major,policy_major):
    if int(plan.schema_version.split(".")[0])!=schema_major or int(plan.policy_version.split(".")[0])!=policy_major:
        raise VisualPlanVersionError("major version incompatible")
    return True
