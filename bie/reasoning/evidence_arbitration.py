from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
 value:str; source_rank:float; directness:float; confidence:float
@dataclass(frozen=True)
class Arbitration:
 winner:str|None; score:float; abstained:bool; rationale:str
def arbitrate(candidates:list[Candidate],threshold=.55,margin=.05)->Arbitration:
 if not candidates:return Arbitration(None,0,True,"no_candidates")
 scored=[]
 for c in candidates:
  if any(v<0 or v>1 for v in (c.source_rank,c.directness,c.confidence)):raise ValueError("normalized evidence required")
  scored.append((.4*c.source_rank+.25*c.directness+.35*c.confidence,c))
 scored.sort(key=lambda x:(-x[0],x[1].value))
 best=scored[0];second=scored[1][0] if len(scored)>1 else 0
 if best[0]<threshold or (len(scored)>1 and best[0]-second<margin):return Arbitration(None,best[0],True,"insufficient_separation")
 return Arbitration(best[1].value,best[0],False,"ranked_evidence_winner")
