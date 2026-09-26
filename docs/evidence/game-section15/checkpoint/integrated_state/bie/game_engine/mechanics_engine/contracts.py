from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from ..canonical import fingerprint
from ..ids import require_id, require_text, require_unique_ids
from ..provenance import ProvenanceBundle
from ..interaction import ActionKind
from ..errors import GameContractError

class MechanicKind(str,Enum):
    MANIPULATE_PARAMETER='manipulate_parameter';DRAG_DROP='drag_and_drop';SPATIAL_ARRANGEMENT='spatial_arrangement';SEQUENCING='sequence_ordering';CLASSIFY_SORT='classify_sort';CONSTRUCT_MODEL='construct_model';SIMULATION_EXPERIMENT='simulation_experiment';GRAPH_EXPLORATION='graph_exploration';TIMELINE_RECONSTRUCTION='timeline_reconstruction';MAP_INTERACTION='map_interaction';EQUATION_BALANCE='equation_balance';PREDICTION_OBSERVE='prediction_then_observe';MISCONCEPTION_TRAP='misconception_trap';DIAGNOSE_ERROR='diagnose_error';BRANCHING_SCENARIO='branching_scenario';RESOURCE_TRADEOFF='resource_tradeoff';RETRIEVAL='retrieval'
class MotionSemantic(str,Enum): VALUE_CHANGE='value_change';TRANSLATE='translate';SNAP='snap';REORDER='reorder';GROUP='group';ASSEMBLE='assemble';TRACE='trace';PLOT='plot';REVEAL='reveal';HIGHLIGHT='highlight';BALANCE='balance';COMPARE='compare';BRANCH='branch';FLOW='flow';FOCUS='focus'
class ReplayPolicy(str,Enum): EXACT='exact';RESETTABLE='resettable';SEEDED='seeded'

@dataclass(frozen=True)
class AccessibilityAction:
    action_id:str;action_kind:ActionKind;accessible_label:str;keyboard_equivalent:str|None;target_ref:str
    def validate(self):
        require_id(self.action_id,'GAME_MECH_ACTION_ID');require_text(self.accessible_label,'GAME_MECH_ACTION_LABEL');require_id(self.target_ref,'GAME_MECH_ACTION_TARGET')
        if type(self.action_kind) is not ActionKind:raise GameContractError('GAME_MECH_ACTION_KIND')
        if self.action_kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.ADJUST,ActionKind.PLACE,ActionKind.ORDER} and not self.keyboard_equivalent:raise GameContractError('GAME_MECH_KEYBOARD_EQUIVALENT_REQUIRED')
        return self
@dataclass(frozen=True)
class SemanticMotion:
    motion_id:str;semantic:MotionSemantic;target_ref:str;pedagogical_purpose:str;state_binding:str|None=None
    def validate(self):
        require_id(self.motion_id,'GAME_MECH_MOTION_ID');require_id(self.target_ref,'GAME_MECH_MOTION_TARGET');require_text(self.pedagogical_purpose,'GAME_MECH_MOTION_PURPOSE')
        if type(self.semantic) is not MotionSemantic:raise GameContractError('GAME_MECH_MOTION_KIND')
        if self.state_binding is not None:require_id(self.state_binding,'GAME_MECH_MOTION_STATE_BINDING')
        return self
@dataclass(frozen=True)
class MechanicQuality:
    anti_slide_default:bool=True;state_causal_motion:bool=True;keyboard_parity:bool=True;non_color_only_feedback:bool=True;answer_reveal_before_attempt:bool=False;speed_pressure_required:bool=False;deterministic_replay:bool=True;product_accepted:bool=False
    def validate(self):
        if not all(x is True for x in (self.anti_slide_default,self.state_causal_motion,self.keyboard_parity,self.non_color_only_feedback,self.deterministic_replay)):raise GameContractError('GAME_MECH_QUALITY_WEAKENED')
        if self.answer_reveal_before_attempt or self.speed_pressure_required or self.product_accepted:raise GameContractError('GAME_MECH_QUALITY_FORBIDDEN')
        return self
@dataclass(frozen=True)
class MechanicDefinition:
    mechanic_id:str;kind:MechanicKind;objective_id:str;pedagogical_intent:str;actions:tuple[AccessibilityAction,...];motion:tuple[SemanticMotion,...];runtime_capabilities:tuple[str,...];evidence_refs:tuple[str,...];replay_policy:ReplayPolicy;reset_supported:bool;quality:MechanicQuality=MechanicQuality();product_accepted:bool=False
    def validate(self):
        require_id(self.mechanic_id,'GAME_MECH_ID');require_id(self.objective_id,'GAME_MECH_OBJECTIVE');require_text(self.pedagogical_intent,'GAME_MECH_INTENT')
        if type(self.kind) is not MechanicKind or type(self.replay_policy) is not ReplayPolicy:raise GameContractError('GAME_MECH_ENUM')
        if not self.actions or not self.motion or not self.runtime_capabilities or not self.evidence_refs:raise GameContractError('GAME_MECH_REQUIRED_COMPONENT')
        require_unique_ids([x.action_id for x in self.actions],'GAME_MECH_ACTION_DUPLICATE');require_unique_ids([x.motion_id for x in self.motion],'GAME_MECH_MOTION_DUPLICATE')
        for x in self.actions:x.validate()
        for x in self.motion:x.validate()
        if self.reset_supported is not True:raise GameContractError('GAME_MECH_RESET_REQUIRED')
        self.quality.validate()
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self
@dataclass(frozen=True)
class MechanicContext:
    objective_id:str;source_refs:tuple[str,...];reasoning_refs:tuple[str,...];provenance:ProvenanceBundle;runtime_capabilities:tuple[str,...]
    def validate(self):
        require_id(self.objective_id,'GAME_MECH_CONTEXT_OBJECTIVE')
        if not self.source_refs or not self.reasoning_refs:raise GameContractError('GAME_MECH_CONTEXT_PROVENANCE')
        self.provenance.validate(('source','reasoning','objective'))
        if not self.runtime_capabilities:raise GameContractError('GAME_MECH_RUNTIME_CAPABILITIES')
        return self
@dataclass(frozen=True)
class MechanicReceipt:
    receipt_id:str;mechanic_id:str;kind:MechanicKind;before_fingerprint:str;after_fingerprint:str;action_fingerprint:str;outcome_fingerprint:str;state_changed:bool;semantic_motion_ids:tuple[str,...];evidence_refs:tuple[str,...];deterministic:bool=True;replay_verified:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.receipt_id,'GAME_MECH_RECEIPT_ID');require_id(self.mechanic_id,'GAME_MECH_RECEIPT_MECHANIC')
        if type(self.kind) is not MechanicKind:raise GameContractError('GAME_MECH_RECEIPT_KIND')
        for h in (self.before_fingerprint,self.after_fingerprint,self.action_fingerprint,self.outcome_fingerprint):
            if not isinstance(h,str) or not h.startswith('sha256:'):raise GameContractError('GAME_MECH_RECEIPT_HASH')
        if not self.semantic_motion_ids or not self.evidence_refs:raise GameContractError('GAME_MECH_RECEIPT_EVIDENCE')
        if not self.state_changed or not self.deterministic or not self.replay_verified or self.product_accepted:raise GameContractError('GAME_MECH_RECEIPT_SCOPE')
        return self

def definition_fingerprint(d:MechanicDefinition)->str:d.validate();return fingerprint(d)
