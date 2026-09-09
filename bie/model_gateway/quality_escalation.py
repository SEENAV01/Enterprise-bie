
from dataclasses import dataclass
class EscalationError(ValueError):pass
@dataclass(frozen=True)
class QualityPolicy:min_confidence:float;max_escalations:int
def next_action(confidence,attempt,p):
 if not 0<=confidence<=1 or not 0<=p.min_confidence<=1 or p.max_escalations<0:raise EscalationError("invalid")
 if confidence>=p.min_confidence:return "ACCEPT"
 if attempt<p.max_escalations:return "ESCALATE"
 return "REVIEW"
