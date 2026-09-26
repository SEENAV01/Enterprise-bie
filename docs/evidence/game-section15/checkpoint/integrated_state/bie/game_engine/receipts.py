from __future__ import annotations
from dataclasses import dataclass
from .canonical import fingerprint
from .ids import require_id
from .errors import GameContractError

@dataclass(frozen=True)
class ValidationReceipt:
    task_id:str; input_fingerprint:str; output_fingerprint:str; implementation_fingerprint:str; deterministic:bool=True; product_accepted:bool=False
    def validate(self):
        require_id(self.task_id,'GAME_RECEIPT_TASK')
        for h in (self.input_fingerprint,self.output_fingerprint,self.implementation_fingerprint):
            if not (isinstance(h,str) and h.startswith('sha256:') and len(h)==71):raise GameContractError('GAME_RECEIPT_HASH')
        if self.deterministic is not True:raise GameContractError('GAME_RECEIPT_DETERMINISM')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def make_receipt(task_id,input_value,output_value,implementation_value):
    return ValidationReceipt(task_id,fingerprint(input_value),fingerprint(output_value),fingerprint(implementation_value)).validate()
