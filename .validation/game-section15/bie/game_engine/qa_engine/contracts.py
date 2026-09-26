from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from ..canonical import fingerprint
from ..ids import require_id,require_text
from .errors import GameQAError
class GateStatus(str,Enum):PASS='pass';FAIL='fail';BLOCKED='blocked'
class Severity(str,Enum):INFO='info';WARNING='warning';ERROR='error';CRITICAL='critical'
@dataclass(frozen=True)
class QualityFinding:
    finding_id:str;severity:Severity;code:str;message:str;evidence_refs:tuple[str,...]=();blocking:bool=False
    def validate(self):
        require_id(self.finding_id,'GAME_QA_FINDING_ID');require_id(self.code,'GAME_QA_FINDING_CODE');require_text(self.message,'GAME_QA_FINDING_MESSAGE')
        if type(self.severity) is not Severity or type(self.blocking) is not bool:raise GameQAError('GAME_QA_FINDING_SHAPE')
        if self.blocking and self.severity not in (Severity.ERROR,Severity.CRITICAL):raise GameQAError('GAME_QA_BLOCKING_SEVERITY')
        return self
@dataclass(frozen=True)
class QualityMetric:
    name:str;value:float;minimum:float|None=None;maximum:float|None=None;unit:str='ratio'
    def validate(self):
        require_id(self.name,'GAME_QA_METRIC_NAME')
        if type(self.value) not in (int,float):raise GameQAError('GAME_QA_METRIC_VALUE')
        if self.minimum is not None and type(self.minimum) not in (int,float):raise GameQAError('GAME_QA_METRIC_MIN_SHAPE')
        if self.maximum is not None and type(self.maximum) not in (int,float):raise GameQAError('GAME_QA_METRIC_MAX_SHAPE')
        if self.minimum is not None and self.maximum is not None and self.minimum>self.maximum:raise GameQAError('GAME_QA_METRIC_RANGE')
        return self
@dataclass(frozen=True)
class QAGateResult:
    task_id:str;status:GateStatus;score:float;metrics:tuple[QualityMetric,...];findings:tuple[QualityFinding,...];evidence_refs:tuple[str,...];input_fingerprint:str;result_fingerprint:str;deterministic:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.task_id,'GAME_QA_TASK_ID')
        if type(self.status) is not GateStatus or type(self.score) not in (int,float) or not 0<=self.score<=1:raise GameQAError('GAME_QA_RESULT_SHAPE')
        [m.validate() for m in self.metrics];[f.validate() for f in self.findings]
        blocking=any(f.blocking for f in self.findings)
        if (self.status is GateStatus.PASS)==blocking:raise GameQAError('GAME_QA_STATUS_FINDING_MISMATCH')
        if not self.evidence_refs or not self.input_fingerprint.startswith('sha256:') or not self.result_fingerprint.startswith('sha256:'):raise GameQAError('GAME_QA_EVIDENCE_REQUIRED')
        if not self.deterministic or self.product_accepted:raise GameQAError('GAME_QA_SCOPE')
        return self
@dataclass(frozen=True)
class GameQAReport:
    results:tuple[QAGateResult,...];report_fingerprint:str;all_passed:bool;implementation_scope_only:bool=True;product_accepted:bool=False
    def validate(self):
        if len(self.results)!=10:raise GameQAError('GAME_QA_REPORT_GATE_COUNT')
        ids=[r.task_id for r in self.results]
        if len(ids)!=len(set(ids)):raise GameQAError('GAME_QA_REPORT_DUPLICATE')
        [r.validate() for r in self.results]
        if self.all_passed is not all(r.status is GateStatus.PASS for r in self.results):raise GameQAError('GAME_QA_REPORT_STATUS')
        if not self.report_fingerprint.startswith('sha256:') or not self.implementation_scope_only or self.product_accepted:raise GameQAError('GAME_QA_REPORT_SCOPE')
        return self

def result(task_id,input_value,score,metrics,findings,evidence_refs):
    metrics=tuple(metrics);findings=tuple(findings);status=GateStatus.FAIL if any(f.blocking for f in findings) else GateStatus.PASS
    body={'task_id':task_id,'status':status.value,'score':round(float(score),6),'metrics':metrics,'findings':findings,'evidence_refs':tuple(sorted(set(evidence_refs))),'input_fingerprint':fingerprint(input_value),'product_accepted':False}
    fp=fingerprint(body)
    return QAGateResult(task_id,status,round(float(score),6),metrics,findings,tuple(sorted(set(evidence_refs))),body['input_fingerprint'],fp,True,False).validate()

def enforce(r):
    r.validate()
    if r.status is not GateStatus.PASS:raise GameQAError('GAME_QA_GATE_FAILED',r.task_id+':'+','.join(f.code for f in r.findings if f.blocking))
    return r
