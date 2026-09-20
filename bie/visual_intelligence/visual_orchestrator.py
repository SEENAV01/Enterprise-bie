from __future__ import annotations
from dataclasses import dataclass
from .visual_plan_contract import STAGES,StageRef,build_plan,append_stage,fp
from .director_handoff_adoption import stage_ref

class OrchestratorError(RuntimeError): pass
class RawSourceRejected(OrchestratorError): pass

@dataclass(frozen=True)
class ExecutionReport:
    completed:tuple[str,...]; blocked_stage:str|None; plan_fingerprint:str|None; review_required:bool=True; accepted:bool=False

class Store:
    def __init__(self): self.data={}
    def put(self,r):
        k=(r.stage,r.artifact_id,r.revision)
        if k in self.data and self.data[k].artifact_fingerprint!=r.artifact_fingerprint: raise OrchestratorError("idempotency conflict")
        self.data[k]=r

class VisualOrchestrator:
    def __init__(self,schema_version="1.0.0",policy_version="1.0.0"):
        self.schema_version=schema_version; self.policy_version=policy_version; self.store=Store(); self.exec={}
    def register(self,stage,fn):
        stage=stage.upper()
        if stage not in STAGES[1:] or stage in self.exec: raise OrchestratorError("invalid/duplicate executor")
        self.exec[stage]=fn
    def run(self,run_id,context,target_profile,stage_inputs=None):
        if any(k in (stage_inputs or {}) for k in ("raw_book","raw_pdf","source_bytes")): raise RawSourceRejected("VIS rejects raw source input")
        first=stage_ref(context); self.store.put(first)
        plan=build_plan(run_id,self.schema_version,self.policy_version,context.source_id,context.source_revision,context.handoff_id,context.handoff_revision,target_profile,[first])
        completed=["DIR_ADOPT"]
        for stage in STAGES[1:]:
            if stage not in self.exec: raise OrchestratorError(f"missing executor {stage}")
            o=self.exec[stage]({"context":context,"prior":plan.stages[-1],"target_profile":target_profile,"stage_inputs":dict(stage_inputs or {})})
            ref=StageRef(stage,o["artifact_id"],o.get("revision",1),
                         o.get("fingerprint") or fp({"stage":stage,"artifact_id":o["artifact_id"],"payload":o.get("payload",{})}),
                         tuple(o.get("evidence_refs",context.evidence_refs)),tuple(o.get("reasoning_refs",context.reasoning_refs)),
                         bool(o.get("current",True)),o.get("status","PASS"),dict(o.get("payload",{})))
            self.store.put(ref); completed.append(stage)
            if ref.status in {"BLOCKED","UNSUPPORTED"} or not ref.current:
                return plan,ExecutionReport(tuple(completed),stage,plan.fingerprint)
            plan=append_stage(plan,ref)
        return plan,ExecutionReport(tuple(completed),None,plan.fingerprint)
