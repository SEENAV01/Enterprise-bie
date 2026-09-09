from dataclasses import dataclass
@dataclass(frozen=True)
class Visual: kind:str; semantic_fit:float; information_density:float; motion_need:float; evidence:str
def decide(items):
 if not items:raise ValueError("visual candidates required")
 for x in items:
  if any(v<0 or v>1 for v in (x.semantic_fit,x.information_density,x.motion_need)):raise ValueError("normalized scores")
  if not x.evidence.strip():raise ValueError("evidence required")
 return max(items,key=lambda x:(.6*x.semantic_fit+.25*(1-abs(x.information_density-.5))+.15*x.motion_need,x.kind))
