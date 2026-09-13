from dataclasses import dataclass
@dataclass(frozen=True)
class RemediationPlan:
    misconception_id:str; sequence:tuple[str,...]; mastery_threshold:float; evidence_ids:tuple[str,...]
def plan_misconception_remediation(misconception_id,correct_model,evidence_ids,mastery_threshold=.8):
    if not misconception_id.strip() or not correct_model.strip() or not evidence_ids or not 0<=mastery_threshold<=1: raise ValueError('inputs')
    return RemediationPlan(misconception_id,('elicit current belief','present grounded contradiction/counterexample','teach replacement model: '+correct_model,'guided application','independent transfer check'),mastery_threshold,tuple(sorted(set(evidence_ids))))
