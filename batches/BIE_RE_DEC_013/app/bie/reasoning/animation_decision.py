from dataclasses import dataclass
@dataclass(frozen=True)
class Animation: intent:str; semantic_need:float; attention_cost:float; evidence:str
def decide(xs):
 if not xs:raise ValueError("animations required")
 for x in xs:
  if not x.evidence or any(v<0 or v>1 for v in (x.semantic_need,x.attention_cost)):raise ValueError("invalid animation")
 return max(xs,key=lambda x:(.8*x.semantic_need-.2*x.attention_cost,x.intent))
