from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

class RunStateError(ValueError): pass

STAGE_STATES={"PENDING","READY","RUNNING","SUCCEEDED","FAILED","BLOCKED","INVALIDATED"}
RUN_STATES={"CREATED","ACTIVE","BLOCKED","EXECUTION_COMPLETE"}

def now()->str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class TransitionEvent:
    stage_id:str
    from_state:str
    to_state:str
    attempt:int
    timestamp:str
    reason:str=""
    evidence_refs:List[str]=field(default_factory=list)

@dataclass
class StageAttempt:
    attempt:int
    state:str="PENDING"
    input_artifact_refs:List[str]=field(default_factory=list)
    output_artifact_refs:List[str]=field(default_factory=list)
    evidence_refs:List[str]=field(default_factory=list)
    diagnostics:List[str]=field(default_factory=list)
    remediation_owner:Optional[str]=None
    started_at:Optional[str]=None
    ended_at:Optional[str]=None

@dataclass
class StageRuntime:
    stage_id:str
    required_predecessors:List[str]
    attempts:List[StageAttempt]=field(default_factory=lambda:[StageAttempt(1)])
    events:List[TransitionEvent]=field(default_factory=list)

    @property
    def current(self)->StageAttempt:return self.attempts[-1]

@dataclass
class RunStateMachine:
    run_id:str
    stages:Dict[str,StageRuntime]
    run_state:str="CREATED"

    def _transition(self,s:StageRuntime,to_state:str,reason:str="",evidence_refs=None)->None:
        if to_state not in STAGE_STATES:raise RunStateError("invalid target state")
        old=s.current.state
        allowed={
          "PENDING":{"READY","BLOCKED"},
          "READY":{"RUNNING","BLOCKED"},
          "RUNNING":{"SUCCEEDED","FAILED","BLOCKED"},
          "FAILED":{"READY","BLOCKED"},
          "SUCCEEDED":{"INVALIDATED"},
          "INVALIDATED":{"READY","BLOCKED"},
          "BLOCKED":{"READY"},
        }
        if to_state not in allowed.get(old,set()):
            raise RunStateError(f"illegal transition {old}->{to_state} for {s.stage_id}")
        s.current.state=to_state
        if to_state=="RUNNING":s.current.started_at=now()
        if to_state in {"SUCCEEDED","FAILED","BLOCKED"}:s.current.ended_at=now()
        refs=list(evidence_refs or [])
        s.events.append(TransitionEvent(s.stage_id,old,to_state,s.current.attempt,now(),reason,refs))

    def predecessors_succeeded(self,stage_id:str)->bool:
        s=self.stages[stage_id]
        return all(p in self.stages and self.stages[p].current.state=="SUCCEEDED" for p in s.required_predecessors)

    def mark_ready(self,stage_id:str)->None:
        s=self.stages[stage_id]
        if not self.predecessors_succeeded(stage_id):
            raise RunStateError("required predecessors have not succeeded")
        self._transition(s,"READY","prerequisites satisfied")
        self.run_state="ACTIVE"

    def start(self,stage_id:str,input_artifact_refs:List[str])->None:
        s=self.stages[stage_id]
        if not input_artifact_refs and s.required_predecessors:
            raise RunStateError("non-root stage requires input artifact refs")
        s.current.input_artifact_refs=list(input_artifact_refs)
        self._transition(s,"RUNNING","stage execution started")

    def succeed(self,stage_id:str,output_artifact_refs:List[str],evidence_refs:List[str])->None:
        s=self.stages[stage_id]
        if not output_artifact_refs:raise RunStateError("success requires output artifact refs")
        if not evidence_refs:raise RunStateError("success requires execution evidence")
        s.current.output_artifact_refs=list(output_artifact_refs)
        s.current.evidence_refs=list(evidence_refs)
        self._transition(s,"SUCCEEDED","stage completed",evidence_refs)
        self._refresh_run_state()

    def fail(self,stage_id:str,diagnostics:List[str],evidence_refs:List[str],remediation_owner:str)->None:
        s=self.stages[stage_id]
        if not diagnostics or not evidence_refs or not remediation_owner:
            raise RunStateError("failure requires diagnostics, evidence and remediation owner")
        s.current.diagnostics=list(diagnostics)
        s.current.evidence_refs=list(evidence_refs)
        s.current.remediation_owner=remediation_owner
        self._transition(s,"FAILED","stage failed",evidence_refs)
        self.run_state="BLOCKED"

    def retry(self,stage_id:str)->None:
        s=self.stages[stage_id]
        if s.current.state!="FAILED":raise RunStateError("only FAILED stage may retry")
        self._transition(s,"READY","retry authorized")
        previous=s.current
        new=StageAttempt(previous.attempt+1,state="READY")
        s.attempts.append(new)
        s.events.append(TransitionEvent(stage_id,"FAILED","READY",new.attempt,now(),"new immutable retry attempt",[]))
        self.run_state="ACTIVE"

    def invalidate(self,stage_id:str,reason:str,evidence_refs:List[str])->None:
        s=self.stages[stage_id]
        if not reason or not evidence_refs:raise RunStateError("invalidation requires reason/evidence")
        self._transition(s,"INVALIDATED",reason,evidence_refs)
        self.run_state="ACTIVE"

    def recover_interrupted(self,stage_id:str,recovery_evidence_ref:str)->None:
        s=self.stages[stage_id]
        if s.current.state!="RUNNING":raise RunStateError("only RUNNING stage is interrupted")
        self.fail(stage_id,["execution interrupted/crash"],[recovery_evidence_ref],"INFRA")

    def _refresh_run_state(self)->None:
        states=[s.current.state for s in self.stages.values()]
        if any(x in {"FAILED","BLOCKED"} for x in states):
            self.run_state="BLOCKED"
        elif all(x=="SUCCEEDED" for x in states):
            self.run_state="EXECUTION_COMPLETE"
        else:self.run_state="ACTIVE"

    def validate(self)->None:
        if not self.run_id:raise RunStateError("run_id required")
        if self.run_state not in RUN_STATES:raise RunStateError("invalid run state")
        for sid,s in self.stages.items():
            if sid!=s.stage_id:raise RunStateError("stage map key mismatch")
            nums=[a.attempt for a in s.attempts]
            if nums!=list(range(1,len(nums)+1)):raise RunStateError("attempt sequence invalid")
            for a in s.attempts:
                if a.state not in STAGE_STATES:raise RunStateError("invalid stage state")

def build_run_state(run_id:str, predecessor_map:Dict[str,List[str]])->RunStateMachine:
    stages={sid:StageRuntime(sid,list(preds)) for sid,preds in predecessor_map.items()}
    return RunStateMachine(run_id,stages)
