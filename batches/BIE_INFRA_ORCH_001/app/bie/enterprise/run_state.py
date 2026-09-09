from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

class RunStateError(ValueError): pass
STAGE_STATES={"PENDING","READY","RUNNING","SUCCEEDED","FAILED","BLOCKED","INVALIDATED"}
RUN_STATES={"CREATED","ACTIVE","BLOCKED","EXECUTION_COMPLETE"}

def now(): return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class TransitionEvent:
    stage_id:str; from_state:str; to_state:str; attempt:int; timestamp:str
    reason:str=""; evidence_refs:List[str]=field(default_factory=list)

@dataclass
class StageAttempt:
    attempt:int; state:str="PENDING"
    input_artifact_refs:List[str]=field(default_factory=list)
    output_artifact_refs:List[str]=field(default_factory=list)
    evidence_refs:List[str]=field(default_factory=list)
    diagnostics:List[str]=field(default_factory=list)
    remediation_owner:Optional[str]=None

@dataclass
class StageRuntime:
    stage_id:str; required_predecessors:List[str]
    attempts:List[StageAttempt]=field(default_factory=lambda:[StageAttempt(1)])
    events:List[TransitionEvent]=field(default_factory=list)
    @property
    def current(self): return self.attempts[-1]

@dataclass
class RunStateMachine:
    run_id:str; stages:Dict[str,StageRuntime]; run_state:str="CREATED"

    def _transition(self,s,to_state,reason="",evidence_refs=None):
        old=s.current.state
        allowed={"PENDING":{"READY","BLOCKED"},"READY":{"RUNNING","BLOCKED"},"RUNNING":{"SUCCEEDED","FAILED","BLOCKED"},
                 "FAILED":{"READY","BLOCKED"},"SUCCEEDED":{"INVALIDATED"},"INVALIDATED":{"READY","BLOCKED"},"BLOCKED":{"READY"}}
        if to_state not in allowed.get(old,set()): raise RunStateError(f"illegal transition {old}->{to_state}")
        s.current.state=to_state
        s.events.append(TransitionEvent(s.stage_id,old,to_state,s.current.attempt,now(),reason,list(evidence_refs or [])))

    def predecessors_succeeded(self,stage_id):
        return all(p in self.stages and self.stages[p].current.state=="SUCCEEDED"
                   for p in self.stages[stage_id].required_predecessors)

    def mark_ready(self,stage_id):
        s=self.stages[stage_id]
        if not self.predecessors_succeeded(stage_id): raise RunStateError("predecessors incomplete")
        self._transition(s,"READY","prerequisites satisfied"); self.run_state="ACTIVE"

    def start(self,stage_id,inputs):
        s=self.stages[stage_id]
        if s.required_predecessors and not inputs: raise RunStateError("non-root stage needs inputs")
        s.current.input_artifact_refs=list(inputs); self._transition(s,"RUNNING","started")

    def succeed(self,stage_id,outputs,evidence):
        if not outputs or not evidence: raise RunStateError("success needs outputs and evidence")
        s=self.stages[stage_id]; s.current.output_artifact_refs=list(outputs); s.current.evidence_refs=list(evidence)
        self._transition(s,"SUCCEEDED","completed",evidence); self._refresh()

    def fail(self,stage_id,diagnostics,evidence,owner):
        if not diagnostics or not evidence or not owner: raise RunStateError("failure needs diagnostics/evidence/owner")
        s=self.stages[stage_id]; s.current.diagnostics=list(diagnostics); s.current.evidence_refs=list(evidence); s.current.remediation_owner=owner
        self._transition(s,"FAILED","failed",evidence); self.run_state="BLOCKED"

    def retry(self,stage_id):
        s=self.stages[stage_id]
        if s.current.state!="FAILED": raise RunStateError("only failed stage can retry")
        n=s.current.attempt+1
        s.attempts.append(StageAttempt(n,state="READY"))
        s.events.append(TransitionEvent(stage_id,"FAILED","READY",n,now(),"immutable retry attempt",[]))
        self.run_state="ACTIVE"

    def _refresh(self):
        states=[s.current.state for s in self.stages.values()]
        if any(x in {"FAILED","BLOCKED"} for x in states): self.run_state="BLOCKED"
        elif all(x=="SUCCEEDED" for x in states): self.run_state="EXECUTION_COMPLETE"
        else: self.run_state="ACTIVE"

def build_run_state(run_id, predecessor_map):
    return RunStateMachine(run_id,{sid:StageRuntime(sid,list(preds)) for sid,preds in predecessor_map.items()})
