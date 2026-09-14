from dataclasses import dataclass
@dataclass(frozen=True)
class AssessmentPrompt: objective_id:str; level:str; prompt:str; success_criterion:str; evidence_ids:tuple[str,...]
def make_assessment_prompt(objective_id,level,label,evidence_ids):
    if not objective_id.strip() or not label.strip() or not evidence_ids: raise ValueError("grounding")
    templates={"REMEMBER":f"State the key idea of {label}.","UNDERSTAND":f"Explain {label} in your own words.","APPLY":f"Apply {label} to a new example.","ANALYZE":f"Analyze how the parts of {label} relate.","EVALUATE":f"Evaluate a claim about {label} using evidence.","CREATE":f"Create a solution or model using {label}."}
    if level not in templates: raise ValueError("level")
    return AssessmentPrompt(objective_id,level,templates[level],"demonstrates requested cognitive operation with grounded reasoning",tuple(sorted(set(evidence_ids))))
