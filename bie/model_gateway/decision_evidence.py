
from dataclasses import dataclass
class DecisionEvidenceError(ValueError):pass
@dataclass(frozen=True)
class DecisionEvidence:
 decision_id:str;candidate_ids:tuple;selected_id:str;reason_codes:tuple;inputs_hash:str
def validate(e):
 if not e.decision_id or not e.candidate_ids or e.selected_id not in e.candidate_ids:raise DecisionEvidenceError("invalid selection")
 if not e.reason_codes or len(e.inputs_hash)!=64:raise DecisionEvidenceError("evidence incomplete")
 return True
