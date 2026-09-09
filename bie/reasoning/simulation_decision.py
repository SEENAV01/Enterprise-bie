from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate: kind:str; causal_value:float; manipulability:float; evidence:str
def decide(xs):
 if not xs:raise ValueError("candidates required")
 for x in xs:
  if not x.evidence or any(v<0 or v>1 for v in (x.causal_value,x.manipulability)):raise ValueError("invalid evidence")
 return max(xs,key=lambda x:(.65*x.causal_value+.35*x.manipulability,x.kind))
