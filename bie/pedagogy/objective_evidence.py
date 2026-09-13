from dataclasses import dataclass
@dataclass(frozen=True)
class ObjectiveEvidence: coverage:float; grounded:bool; requires_review:bool
def objective_evidence(required,bound):
 r=set(required); b=set(bound)
 if not r: raise ValueError("required evidence")
 c=len(r&b)/len(r); return ObjectiveEvidence(c,c==1,c<1)
