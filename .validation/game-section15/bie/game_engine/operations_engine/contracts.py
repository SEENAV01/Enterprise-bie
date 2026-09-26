from __future__ import annotations
from dataclasses import dataclass
import re
from ..ids import require_id
from .errors import GameOperationsError
_SHA=re.compile(r'^[0-9a-f]{64}$')

@dataclass(frozen=True)
class TelemetryConsent:
    enabled:bool; policy_id:str; retention_days:int=30
    def validate(self):
        require_id(self.policy_id,'GAME_OPS_TELEMETRY_POLICY')
        if type(self.enabled) is not bool or type(self.retention_days) is not int or not 1<=self.retention_days<=365:raise GameOperationsError('GAME_OPS_TELEMETRY_CONSENT')
        return self

@dataclass(frozen=True)
class SessionOutcome:
    objective_id:str; challenge_id:str; event_type:str; outcome_code:str; mechanic_id:str; attempt_number:int; mastery_weight:float; evidence_strength:float; adaptation_ids:tuple[str,...]=(); game_id:str|None=None; level_id:str|None=None
    def validate(self):
        for v,c in ((self.objective_id,'GAME_OPS_OBJECTIVE'),(self.challenge_id,'GAME_OPS_CHALLENGE'),(self.event_type,'GAME_OPS_EVENT'),(self.outcome_code,'GAME_OPS_OUTCOME'),(self.mechanic_id,'GAME_OPS_MECHANIC')):require_id(v,c)
        if (self.game_id is None)!=(self.level_id is None):raise GameOperationsError('GAME_OPS_OUTCOME_SCOPE_PARTIAL')
        if self.game_id is not None:require_id(self.game_id,'GAME_OPS_GAME');require_id(self.level_id,'GAME_OPS_LEVEL')
        if self.outcome_code not in {'applied','correct','success','mastered','succeeded','incorrect','failed','failure'}:raise GameOperationsError('GAME_OPS_TERMINAL_OUTCOME_REQUIRED')
        if type(self.attempt_number) is not int or self.attempt_number<1:raise GameOperationsError('GAME_OPS_ATTEMPT')
        for v in (self.mastery_weight,self.evidence_strength):
            if type(v) not in (int,float) or not 0<v<=1:raise GameOperationsError('GAME_OPS_EVIDENCE_WEIGHT')
        for a in self.adaptation_ids:require_id(a,'GAME_OPS_ADAPTATION')
        return self

@dataclass(frozen=True)
class EnterpriseSessionRequest:
    run_context:object; session_id:str; learner_key_hash:str; idempotency_key:str; owner:str; consent:TelemetryConsent; outcomes:tuple[SessionOutcome,...]
    def validate(self):
        self.run_context.validate(); require_id(self.session_id,'GAME_OPS_SESSION');require_id(self.idempotency_key,'GAME_OPS_IDEMPOTENCY');require_id(self.owner,'GAME_OPS_OWNER');self.consent.validate()
        if not _SHA.fullmatch(self.learner_key_hash):raise GameOperationsError('GAME_OPS_LEARNER_HASH')
        if not self.outcomes:raise GameOperationsError('GAME_OPS_OUTCOMES_REQUIRED')
        for x in self.outcomes:x.validate()
        if len({(x.game_id,x.level_id,x.challenge_id,x.attempt_number) for x in self.outcomes})!=len(self.outcomes):raise GameOperationsError('GAME_OPS_DUPLICATE_OUTCOME')
        return self

@dataclass(frozen=True)
class MasteryRecord:
    learner_key_hash:str; objective_id:str; estimate:float; confidence:float; attempts:int; evidence_count:int; version:int; last_event_id:str
    def validate(self):
        if not _SHA.fullmatch(self.learner_key_hash):raise GameOperationsError('GAME_OPS_LEARNER_HASH')
        require_id(self.objective_id,'GAME_OPS_OBJECTIVE'); require_id(self.last_event_id,'GAME_OPS_EVENT_ID')
        if not 0<=self.estimate<=1 or not 0<=self.confidence<=1 or self.attempts<0 or self.evidence_count<1 or self.version<1:raise GameOperationsError('GAME_OPS_MASTERY_RECORD')
        return self

@dataclass(frozen=True)
class EnterpriseSessionResult:
    run_id:str; session_id:str; result_artifact_id:str; build_artifact_id:str; telemetry_artifact_id:str|None; learning_artifact_id:str; mastery:tuple[MasteryRecord,...]; adaptation_actions:tuple[tuple[str,str],...]; idempotent_replay:bool; resumed_from_checkpoint:bool; product_accepted:bool=False
    def validate(self):
        for v,c in ((self.session_id,'GAME_OPS_SESSION'),(self.result_artifact_id,'GAME_OPS_RESULT_ARTIFACT'),(self.build_artifact_id,'GAME_OPS_BUILD_ARTIFACT'),(self.learning_artifact_id,'GAME_OPS_LEARNING_ARTIFACT')):require_id(v,c)
        if self.telemetry_artifact_id is not None:require_id(self.telemetry_artifact_id,'GAME_OPS_TELEMETRY_ARTIFACT')
        if not self.mastery or self.product_accepted:raise GameOperationsError('GAME_OPS_RESULT_SCOPE')
        for m in self.mastery:m.validate()
        return self
