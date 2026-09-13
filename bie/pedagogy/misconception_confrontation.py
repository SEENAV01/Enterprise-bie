from dataclasses import dataclass
@dataclass(frozen=True)
class ConfrontationPlan:
    misconception_id:str; elicitation_prompt:str; conflict_demo:str; replacement_model:str; evidence_ids:tuple[str,...]
def plan_confrontation(misconception_id,claim,counterevidence,replacement_model,evidence_ids):
    if not all(str(x).strip() for x in (misconception_id,claim,counterevidence,replacement_model)) or not evidence_ids: raise ValueError('grounding')
    return ConfrontationPlan(misconception_id,'Predict what follows if this belief is true: '+claim,counterevidence,replacement_model,tuple(sorted(set(evidence_ids))))
