from dataclasses import dataclass
@dataclass(frozen=True)
class TeachingStep:
 expression:str; explain:bool; reason:str; emphasis:tuple[str,...]
def plan_step(expression,concept_load:int,new_rule:bool,misconception_risk:bool,emphasis=()):
 if not expression.strip():raise ValueError("expression required")
 if concept_load<0:raise ValueError("invalid load")
 explain=new_rule or misconception_risk or concept_load>1
 reasons=[]
 if new_rule:reasons.append("new_rule")
 if misconception_risk:reasons.append("misconception_risk")
 if concept_load>1:reasons.append("high_concept_load")
 return TeachingStep(expression,explain,"+".join(reasons) if reasons else "routine_step",tuple(emphasis))
