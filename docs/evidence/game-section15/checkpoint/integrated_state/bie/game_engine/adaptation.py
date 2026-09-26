from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .expressions import Expr, validate_expr
from .ids import require_id, require_unique_ids
from .state import StateModel
from .errors import GameContractError

class AdaptAction(str,Enum): ADVANCE='advance';REPEAT='repeat';REMEDIATE='remediate';EASIER='easier';HARDER='harder';UNLOCK_HINT='unlock_hint';BRANCH='branch'
@dataclass(frozen=True)
class AdaptationRule:
    adaptation_id:str; condition:Expr; action:AdaptAction; priority:int; target_id:str|None=None
    def validate(self,state:StateModel):
        require_id(self.adaptation_id,'GAME_ADAPT_ID');validate_expr(self.condition,state.type_map())
        if type(self.action) is not AdaptAction:raise GameContractError('GAME_ADAPT_ACTION')
        if type(self.priority) is not int or self.priority<0:raise GameContractError('GAME_ADAPT_PRIORITY')
        if self.action in {AdaptAction.UNLOCK_HINT,AdaptAction.BRANCH,AdaptAction.REMEDIATE} and not self.target_id:raise GameContractError('GAME_ADAPT_TARGET')
        return self
@dataclass(frozen=True)
class AdaptationContract:
    rules:tuple[AdaptationRule,...]=()
    def validate(self,state:StateModel):
        require_unique_ids([r.adaptation_id for r in self.rules],'GAME_ADAPT_DUPLICATE')
        priorities=[r.priority for r in self.rules]
        if len(priorities)!=len(set(priorities)):raise GameContractError('GAME_ADAPT_PRIORITY_TIE')
        for r in self.rules:r.validate(state)
        return self
