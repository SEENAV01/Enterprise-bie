from dataclasses import dataclass
@dataclass(frozen=True)
class ContextLink:
 equation_id:str; concept_id:str; paragraph_id:str; evidence:str; confidence:float
def ground_equation(equation_id,concept_id,paragraph_id,evidence,confidence)->ContextLink:
 vals=(equation_id,concept_id,paragraph_id,evidence)
 if not all(str(v).strip() for v in vals):raise ValueError("complete grounding required")
 c=float(confidence)
 if not 0<=c<=1:raise ValueError("confidence out of range")
 return ContextLink(equation_id,concept_id,paragraph_id,evidence,c)
def best_grounding(links):
 if not links:return None
 return sorted(links,key=lambda x:(-x.confidence,x.paragraph_id))[0]
