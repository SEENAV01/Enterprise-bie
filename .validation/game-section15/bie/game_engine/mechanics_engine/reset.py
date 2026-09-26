from __future__ import annotations
from dataclasses import dataclass
from ..canonical import fingerprint
from ..ids import require_id
from ..errors import GameContractError
@dataclass(frozen=True)
class ResetReceipt:
    mechanic_id:str;from_fingerprint:str;to_fingerprint:str;reset_fingerprint:str;deterministic:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.mechanic_id,'GAME_MECH_RESET_ID')
        if any(not x.startswith('sha256:') for x in (self.from_fingerprint,self.to_fingerprint,self.reset_fingerprint)):raise GameContractError('GAME_MECH_RESET_HASH')
        if not self.deterministic or self.product_accepted:raise GameContractError('GAME_MECH_RESET_SCOPE')
        return self

def reset(mechanic_id,current,initial):
    if current==initial:raise GameContractError('GAME_MECH_RESET_NOOP')
    body={'mechanic_id':mechanic_id,'from':current,'to':initial}
    return dict(initial),ResetReceipt(mechanic_id,fingerprint(current),fingerprint(initial),fingerprint(body),True,False).validate()
