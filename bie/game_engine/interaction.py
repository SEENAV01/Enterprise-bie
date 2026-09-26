from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from .ids import require_id, require_text, require_unique_ids
from .expressions import Expr, validate_expr
from .state import StateModel
from .errors import GameContractError

class ActionKind(str,Enum):
    TAP='tap';DRAG='drag';DROP='drop';ADJUST='adjust';SELECT='select';TYPE='type';CONNECT='connect';ORDER='order';PLACE='place';PREDICT='predict';SUBMIT='submit';RESET='reset'
class EffectKind(str,Enum): SET='set';ADD='add';SUB='sub';MUL='mul';DIV='div';TOGGLE='toggle'

@dataclass(frozen=True)
class ActionSpec:
    action_id:str; kind:ActionKind; target_entity_id:str; accessible_label:str
    keyboard_equivalent:str|None=None
    def validate(self):
        require_id(self.action_id,'GAME_ACTION_ID');require_id(self.target_entity_id,'GAME_ACTION_TARGET');require_text(self.accessible_label,'GAME_ACTION_ACCESSIBLE_LABEL')
        if type(self.kind) is not ActionKind:raise GameContractError('GAME_ACTION_KIND')
        if self.kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.ADJUST,ActionKind.PLACE} and not self.keyboard_equivalent:raise GameContractError('GAME_ACTION_KEYBOARD_EQUIVALENT')
        return self

@dataclass(frozen=True)
class EffectSpec:
    target_variable_id:str; kind:EffectKind; value:Any
    def validate(self,state:StateModel):
        require_id(self.target_variable_id,'GAME_EFFECT_TARGET')
        if self.target_variable_id not in state.type_map():raise GameContractError('GAME_EFFECT_TARGET_MISSING')
        if type(self.kind) is not EffectKind:raise GameContractError('GAME_EFFECT_KIND')
        if self.kind==EffectKind.DIV and self.value==0:raise GameContractError('GAME_EFFECT_DIV_ZERO')
        return self

@dataclass(frozen=True)
class RuleSpec:
    rule_id:str; condition:Expr; effects:tuple[EffectSpec,...]; explanation:str; priority:int; grounding_refs:tuple[str,...]
    def validate(self,state:StateModel):
        require_id(self.rule_id,'GAME_RULE_ID');require_text(self.explanation,'GAME_RULE_EXPLANATION')
        validate_expr(self.condition,state.type_map())
        if not self.effects:raise GameContractError('GAME_RULE_EFFECTS_REQUIRED')
        for e in self.effects:e.validate(state)
        if type(self.priority) is not int:raise GameContractError('GAME_RULE_PRIORITY')
        if not self.grounding_refs:raise GameContractError('GAME_RULE_GROUNDING')
        return self

@dataclass(frozen=True)
class InteractionContract:
    actions:tuple[ActionSpec,...]; rules:tuple[RuleSpec,...]
    def validate(self,state:StateModel):
        if not self.actions:raise GameContractError('GAME_ACTIONS_REQUIRED')
        require_unique_ids([a.action_id for a in self.actions],'GAME_ACTION_DUPLICATE');require_unique_ids([r.rule_id for r in self.rules],'GAME_RULE_DUPLICATE')
        for a in self.actions:a.validate()
        for r in self.rules:r.validate(state)
        return self
