from dataclasses import dataclass
@dataclass(frozen=True)
class Example: id:str; concept_coverage:float; difficulty:float; source_grounding:float
def decide(items,target_difficulty):
 if not 0<=target_difficulty<=1:raise ValueError("target difficulty")
 if not items:raise ValueError("examples required")
 for x in items:
  if any(v<0 or v>1 for v in (x.concept_coverage,x.difficulty,x.source_grounding)):raise ValueError("normalized scores")
 return max(items,key=lambda x:(.45*x.concept_coverage+.35*x.source_grounding-.2*abs(x.difficulty-target_difficulty),x.id))
