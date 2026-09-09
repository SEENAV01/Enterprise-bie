from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate: kind:str; semantic_fit:float; cognitive_fit:float; evidence:str
def decide(items):
 if not items:raise ValueError("candidates required")
 if any(not 0<=v<=1 for x in items for v in (x.semantic_fit,x.cognitive_fit)):raise ValueError("normalized scores")
 if any(not x.evidence.strip() for x in items):raise ValueError("evidence required")
 return max(items,key=lambda x:(.65*x.semantic_fit+.35*x.cognitive_fit,x.kind))
