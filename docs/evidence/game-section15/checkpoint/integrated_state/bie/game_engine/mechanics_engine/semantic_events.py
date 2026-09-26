from __future__ import annotations
from dataclasses import dataclass
from ..ids import require_id,require_text
from ..canonical import fingerprint
from .contracts import MechanicReceipt,MechanicDefinition
from .errors import MechanicError
@dataclass(frozen=True)
class SemanticInteractionEvent:
    event_id:str;mechanic_id:str;receipt_id:str;motion_ids:tuple[str,...];state_before:str;state_after:str;pedagogical_purpose:str;causal:bool=True;decorative_only:bool=False;product_accepted:bool=False
    def validate(self):
        for x,c in ((self.event_id,'GAME_MECH_EVENT_ID'),(self.mechanic_id,'GAME_MECH_EVENT_MECHANIC'),(self.receipt_id,'GAME_MECH_EVENT_RECEIPT')):require_id(x,c)
        require_text(self.pedagogical_purpose,'GAME_MECH_EVENT_PURPOSE')
        if not self.motion_ids or not self.state_before.startswith('sha256:') or not self.state_after.startswith('sha256:'):raise MechanicError('GAME_MECH_EVENT_BINDING')
        if not self.causal or self.decorative_only or self.product_accepted:raise MechanicError('GAME_MECH_EVENT_QUALITY')
        return self

def from_receipt(defn:MechanicDefinition,receipt:MechanicReceipt):
    defn.validate();receipt.validate()
    if defn.mechanic_id!=receipt.mechanic_id:raise MechanicError('GAME_MECH_EVENT_MECHANIC_MISMATCH')
    purpose='; '.join(m.pedagogical_purpose for m in defn.motion)
    body={'mechanic':defn.mechanic_id,'receipt':receipt.receipt_id,'motion_ids':receipt.semantic_motion_ids,'before':receipt.before_fingerprint,'after':receipt.after_fingerprint}
    return SemanticInteractionEvent('event:'+fingerprint(body)[7:31],defn.mechanic_id,receipt.receipt_id,receipt.semantic_motion_ids,receipt.before_fingerprint,receipt.after_fingerprint,purpose,True,False,False).validate()
