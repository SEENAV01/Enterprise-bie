from __future__ import annotations
from dataclasses import dataclass
from ..canonical import fingerprint
from ..ids import require_id
from .contracts import QAGateResult
from .errors import GameQAError
@dataclass(frozen=True)
class QAReceipt:
    receipt_id:str;task_id:str;result_fingerprint:str;implementation_fingerprint:str;deterministic:bool=True;product_accepted:bool=False
    def validate(self):
        require_id(self.receipt_id,'GAME_QA_RECEIPT_ID');require_id(self.task_id,'GAME_QA_RECEIPT_TASK')
        if not self.result_fingerprint.startswith('sha256:') or not self.implementation_fingerprint.startswith('sha256:') or not self.deterministic or self.product_accepted:raise GameQAError('GAME_QA_RECEIPT_SCOPE')
        return self
def make_receipt(result:QAGateResult,implementation):
    rid='qa-receipt:'+fingerprint((result.task_id,result.result_fingerprint,implementation))[7:31]
    return QAReceipt(rid,result.task_id,result.result_fingerprint,fingerprint(implementation),True,False).validate()
