from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from ..canonical import fingerprint
from ..ids import require_id, require_text
from ..errors import GameContractError
from ..expressions import Expr

class ChallengeStatus(str,Enum):
    LOCKED='locked'; READY='ready'; ACTIVE='active'; SUCCEEDED='succeeded'; FAILED='failed'

@dataclass(frozen=True)
class StateSnapshot:
    snapshot_id:str
    tick:int
    values:tuple[tuple[str,Any],...]
    schema_fingerprint:str
    parent_snapshot_id:str|None=None
    transition_receipt_id:str|None=None
    product_accepted:bool=False
    def validate(self):
        require_id(self.snapshot_id,'GAME_STATE_SNAPSHOT_ID')
        if type(self.tick) is not int or self.tick<0:raise GameContractError('GAME_STATE_SNAPSHOT_TICK')
        keys=[k for k,_ in self.values]
        if keys!=sorted(keys) or len(keys)!=len(set(keys)):raise GameContractError('GAME_STATE_SNAPSHOT_KEYS')
        if not self.schema_fingerprint.startswith('sha256:'):raise GameContractError('GAME_STATE_SCHEMA_FINGERPRINT')
        if self.parent_snapshot_id is not None:require_id(self.parent_snapshot_id,'GAME_STATE_PARENT_ID')
        if self.transition_receipt_id is not None:require_id(self.transition_receipt_id,'GAME_STATE_TRANSITION_RECEIPT_ID')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self
    def as_dict(self):return dict(self.values)

@dataclass(frozen=True)
class ActionCommand:
    command_id:str; sequence_no:int; action_id:str; actor_ref:str; payload:tuple[tuple[str,Any],...]=(); expected_snapshot_id:str|None=None
    def validate(self):
        require_id(self.command_id,'GAME_STATE_COMMAND_ID');require_id(self.action_id,'GAME_STATE_ACTION_ID');require_id(self.actor_ref,'GAME_STATE_ACTOR_REF')
        if type(self.sequence_no) is not int or self.sequence_no<0:raise GameContractError('GAME_STATE_COMMAND_SEQUENCE')
        keys=[k for k,_ in self.payload]
        if keys!=sorted(keys) or len(keys)!=len(set(keys)):raise GameContractError('GAME_STATE_COMMAND_PAYLOAD')
        if self.expected_snapshot_id is not None:require_id(self.expected_snapshot_id,'GAME_STATE_EXPECTED_SNAPSHOT_ID')
        return self

@dataclass(frozen=True)
class CompiledAction:
    action_id:str; kind:str; target_entity_id:str; accessible_label:str; keyboard_equivalent:str|None
    def validate(self):
        for v,c in ((self.action_id,'GAME_STATE_ACTION_ID'),(self.kind,'GAME_STATE_ACTION_KIND'),(self.target_entity_id,'GAME_STATE_ACTION_TARGET')):require_id(v,c)
        require_text(self.accessible_label,'GAME_STATE_ACTION_ACCESSIBLE_LABEL')
        return self

@dataclass(frozen=True)
class CompiledRule:
    rule_id:str; priority:int; condition:Expr; effect_count:int; grounding_refs:tuple[str,...]
    def validate(self):
        require_id(self.rule_id,'GAME_STATE_RULE_ID')
        if type(self.priority) is not int:raise GameContractError('GAME_STATE_RULE_PRIORITY')
        if type(self.effect_count) is not int or self.effect_count<=0:raise GameContractError('GAME_STATE_RULE_EFFECT_COUNT')
        if not self.grounding_refs:raise GameContractError('GAME_STATE_RULE_GROUNDING')
        return self

@dataclass(frozen=True)
class StateDelta:
    variable_id:str; before:Any; after:Any; operation:str
    def validate(self):
        require_id(self.variable_id,'GAME_STATE_DELTA_VARIABLE');require_id(self.operation,'GAME_STATE_DELTA_OPERATION')
        if self.before==self.after:raise GameContractError('GAME_STATE_NOOP_DELTA')
        return self

@dataclass(frozen=True)
class ConditionEvaluation:
    challenge_id:str; success:bool; failed:bool; matched_failure_indexes:tuple[int,...]; state_fingerprint:str; product_accepted:bool=False
    def validate(self):
        require_id(self.challenge_id,'GAME_STATE_CONDITION_CHALLENGE')
        if type(self.success) is not bool or type(self.failed) is not bool:raise GameContractError('GAME_STATE_CONDITION_BOOL')
        if self.success and self.failed:raise GameContractError('GAME_STATE_CONDITION_CONFLICT')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class ChallengeProgress:
    challenge_id:str; status:ChallengeStatus; attempts:int; hints_used:int; last_snapshot_id:str; history_fingerprint:str; product_accepted:bool=False
    def validate(self):
        require_id(self.challenge_id,'GAME_STATE_CHALLENGE_ID');require_id(self.last_snapshot_id,'GAME_STATE_CHALLENGE_SNAPSHOT')
        if type(self.status) is not ChallengeStatus:raise GameContractError('GAME_STATE_CHALLENGE_STATUS')
        if type(self.attempts) is not int or self.attempts<0 or type(self.hints_used) is not int or self.hints_used<0:raise GameContractError('GAME_STATE_CHALLENGE_COUNTERS')
        if not self.history_fingerprint.startswith('sha256:'):raise GameContractError('GAME_STATE_CHALLENGE_HISTORY')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

@dataclass(frozen=True)
class TransitionReceipt:
    receipt_id:str; command_id:str; rule_id:str; before_snapshot_id:str; after_snapshot_id:str; deltas:tuple[StateDelta,...]; before_fingerprint:str; after_fingerprint:str; implementation_fingerprint:str; deterministic:bool=True; product_accepted:bool=False
    def validate(self):
        for v,c in ((self.receipt_id,'GAME_STATE_RECEIPT_ID'),(self.command_id,'GAME_STATE_RECEIPT_COMMAND'),(self.rule_id,'GAME_STATE_RECEIPT_RULE'),(self.before_snapshot_id,'GAME_STATE_RECEIPT_BEFORE'),(self.after_snapshot_id,'GAME_STATE_RECEIPT_AFTER')):require_id(v,c)
        if not self.deltas:raise GameContractError('GAME_STATE_RECEIPT_DELTAS')
        for d in self.deltas:d.validate()
        for h in (self.before_fingerprint,self.after_fingerprint,self.implementation_fingerprint):
            if not h.startswith('sha256:'):raise GameContractError('GAME_STATE_RECEIPT_HASH')
        if self.deterministic is not True or self.product_accepted is not False:raise GameContractError('GAME_STATE_RECEIPT_SCOPE')
        return self
