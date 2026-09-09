from dataclasses import dataclass
@dataclass(frozen=True)
class Evidence:
 source:str; weight:float; kind:str
@dataclass(frozen=True)
class EvidenceSummary:
 confidence:float; sources:tuple[str,...]; kinds:tuple[str,...]
def aggregate_misconception_evidence(items:list[Evidence])->EvidenceSummary:
 for e in items:
  if not 0<=e.weight<=1: raise ValueError("weight out of range")
 unique={(e.source,e.kind):e for e in items}; p=1.0
 for e in unique.values(): p*=1-e.weight
 return EvidenceSummary(round(1-p,6),tuple(sorted({e.source for e in unique.values()})),tuple(sorted({e.kind for e in unique.values()})))
