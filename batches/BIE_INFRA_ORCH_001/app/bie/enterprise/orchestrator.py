from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
import hashlib, json
from .run_state import RunStateMachine

class OrchestratorError(ValueError): pass

@dataclass(frozen=True)
class ExecutionContext:
    run_id:str; stage_id:str; attempt:int; idempotency_key:str
    input_artifact_refs:List[str]
    configuration:Dict[str,Any]=field(default_factory=dict)
    metadata:Dict[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class StageExecutionResult:
    output_artifact_refs:List[str]; evidence_refs:List[str]
    diagnostics:List[str]=field(default_factory=list)
    metadata:Dict[str,Any]=field(default_factory=dict)
    def validate(self):
        if not self.output_artifact_refs: raise OrchestratorError("success requires outputs")
        if not self.evidence_refs: raise OrchestratorError("success requires evidence")

class StageExecutionFailure(Exception):
    def __init__(self,diagnostics,evidence_refs,remediation_owner):
        super().__init__("stage execution failed")
        if not diagnostics or not evidence_refs or not remediation_owner:
            raise OrchestratorError("structured failure incomplete")
        self.diagnostics=list(diagnostics); self.evidence_refs=list(evidence_refs); self.remediation_owner=remediation_owner

@dataclass(frozen=True)
class StageDefinition:
    stage_id:str; predecessors:List[str]; input_types:List[str]; output_type:str; remediation_owner:str
    def validate(self):
        if not self.stage_id or not self.output_type or not self.remediation_owner: raise OrchestratorError("bad stage definition")

class InMemoryArtifactResolver:
    def __init__(self): self._outputs={}
    def outputs_for_stage(self,run_id,stage_id): return list(self._outputs.get((run_id,stage_id),[]))
    def register_stage_outputs(self,run_id,stage_id,refs):
        if not refs: raise OrchestratorError("empty outputs")
        self._outputs[(run_id,stage_id)]=list(refs)

class EnterpriseOrchestrator:
    def __init__(self,state,definitions,executors,artifacts,configuration=None):
        self.state=state; self.definitions=definitions; self.executors=executors; self.artifacts=artifacts
        self.configuration=dict(configuration or {}); self._validate_registry()

    def _validate_registry(self):
        for sid,r in self.state.stages.items():
            if sid not in self.definitions: raise OrchestratorError(f"missing definition {sid}")
            d=self.definitions[sid]; d.validate()
            if set(d.predecessors)!=set(r.required_predecessors): raise OrchestratorError(f"predecessor mismatch {sid}")
        for sid in self.executors:
            if sid not in self.state.stages: raise OrchestratorError(f"executor for unknown stage {sid}")

    def _idempotency_key(self,stage_id,attempt,inputs):
        material={"run_id":self.state.run_id,"stage_id":stage_id,"attempt":attempt,
                  "inputs":sorted(inputs),"configuration":self.configuration}
        return hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

    def _resolve_inputs(self,stage_id):
        refs=[]
        for pred in self.definitions[stage_id].predecessors:
            out=self.artifacts.outputs_for_stage(self.state.run_id,pred)
            if not out: raise OrchestratorError(f"missing artifacts from {pred}")
            refs.extend(out)
        return refs

    def runnable_stages(self):
        out=[]
        for sid in sorted(self.state.stages):
            s=self.state.stages[sid]
            if s.current.state=="READY" or (s.current.state=="PENDING" and self.state.predecessors_succeeded(sid)):
                out.append(sid)
        return out

    def execute_stage(self,stage_id):
        if stage_id not in self.executors: raise OrchestratorError(f"no executor {stage_id}")
        s=self.state.stages[stage_id]
        if s.current.state=="PENDING": self.state.mark_ready(stage_id)
        if s.current.state!="READY": raise OrchestratorError("stage not READY")
        inputs=self._resolve_inputs(stage_id); self.state.start(stage_id,inputs); attempt=s.current.attempt
        ctx=ExecutionContext(self.state.run_id,stage_id,attempt,self._idempotency_key(stage_id,attempt,inputs),
                             inputs,self.configuration,{"predecessors":self.definitions[stage_id].predecessors})
        try:
            result=self.executors[stage_id](ctx); result.validate()
            self.artifacts.register_stage_outputs(self.state.run_id,stage_id,result.output_artifact_refs)
            self.state.succeed(stage_id,result.output_artifact_refs,result.evidence_refs)
            return result
        except StageExecutionFailure as e:
            self.state.fail(stage_id,e.diagnostics,e.evidence_refs,e.remediation_owner); raise
        except Exception as e:
            diag=[f"{type(e).__name__}: {e}"]; ev=[f"orchestrator-exception:{self.state.run_id}:{stage_id}:attempt-{attempt}"]
            owner=self.definitions[stage_id].remediation_owner
            self.state.fail(stage_id,diag,ev,owner)
            raise StageExecutionFailure(diag,ev,owner) from e

    def run_until_blocked_or_complete(self,max_steps=1000):
        executed=[]
        for _ in range(max_steps):
            if self.state.run_state in {"BLOCKED","EXECUTION_COMPLETE"}: return executed
            runnable=[s for s in self.runnable_stages() if s in self.executors]
            if not runnable:
                pending=[sid for sid,s in self.state.stages.items() if s.current.state!="SUCCEEDED"]
                if pending: raise OrchestratorError(f"orchestration stalled: {sorted(pending)}")
                return executed
            sid=runnable[0]
            try:
                self.execute_stage(sid); executed.append(sid)
            except StageExecutionFailure:
                return executed
        raise OrchestratorError("max steps exceeded")

    def retry_failed(self,stage_id): self.state.retry(stage_id)

    def resume(self):
        running=[sid for sid,s in self.state.stages.items() if s.current.state=="RUNNING"]
        if running: raise OrchestratorError(f"interrupted RUNNING stages require recovery: {running}")
        return self.run_until_blocked_or_complete()
