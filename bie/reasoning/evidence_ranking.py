from dataclasses import dataclass
@dataclass(frozen=True)
class RankedEvidence:
 evidence_id:str; relevance:float; reliability:float; directness:float
 @property
 def score(self):return .45*self.relevance+.35*self.reliability+.20*self.directness
def rank_evidence(items:list[RankedEvidence])->tuple[RankedEvidence,...]:
 for x in items:
  if any(v<0 or v>1 for v in (x.relevance,x.reliability,x.directness)):raise ValueError("normalized scores required")
 return tuple(sorted(items,key=lambda x:(-x.score,x.evidence_id)))
