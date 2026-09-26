from __future__ import annotations
from dataclasses import dataclass
from ..expressions import Expr
from ..ids import require_id,require_text
from ..errors import GameContractError
from .expression_runtime import evaluate_typed

@dataclass(frozen=True)
class StateInvariant:
    invariant_id:str; expression:Expr; explanation:str
    def validate(self):require_id(self.invariant_id,'GAME_STATE_INVARIANT_ID');require_text(self.explanation,'GAME_STATE_INVARIANT_EXPLANATION');return self

def verify_invariants(model,snapshot,invariants):
    invariants=tuple(invariants);failures=[]
    for inv in invariants:
        inv.validate();v=evaluate_typed(inv.expression,snapshot.as_dict(),model.type_map())
        if type(v) is not bool:raise GameContractError('GAME_STATE_INVARIANT_NOT_BOOL',inv.invariant_id)
        if not v:failures.append(inv.invariant_id)
    if failures:raise GameContractError('GAME_STATE_INVARIANT_FAILED',','.join(failures))
    return {'verified':len(invariants),'failures':(), 'product_accepted':False}
