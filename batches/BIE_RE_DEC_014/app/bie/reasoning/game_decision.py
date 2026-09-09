from dataclasses import dataclass
@dataclass(frozen=True)
class Game: mechanic:str; objective_fit:float; retrieval_value:float; misconception_value:float
def decide(xs):
 if not xs:raise ValueError("game candidates required")
 for x in xs:
  if any(v<0 or v>1 for v in (x.objective_fit,x.retrieval_value,x.misconception_value)):raise ValueError("normalized scores")
 return max(xs,key=lambda x:(.5*x.objective_fit+.3*x.retrieval_value+.2*x.misconception_value,x.mechanic))
