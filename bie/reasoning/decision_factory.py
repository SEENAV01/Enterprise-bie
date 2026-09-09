from dataclasses import dataclass
@dataclass(frozen=True)
class ReasoningDecision:
 decision_id:str; decision_type:str; choice:str|None; evidence_ids:tuple[str,...]; confidence:float; rationale:str; abstained:bool
ALLOWED={"prerequisite","teaching_order","causal","derivation","misconception","representation","example","assessment","remediation","visual","simulation","animation","game"}
def make_decision(decision_id,decision_type,choice,evidence_ids,confidence,rationale,abstained=False):
 if decision_type not in ALLOWED:raise ValueError("unsupported decision type")
 if not decision_id.strip() or not rationale.strip():raise ValueError("audit fields required")
 c=float(confidence)
 if not 0<=c<=1:raise ValueError("confidence out of range")
 if not abstained and (choice is None or not evidence_ids):raise ValueError("non-abstained decision requires choice and evidence")
 return ReasoningDecision(decision_id,decision_type,choice,tuple(evidence_ids),c,rationale,abstained)
