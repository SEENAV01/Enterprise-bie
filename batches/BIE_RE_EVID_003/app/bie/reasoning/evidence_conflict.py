from dataclasses import dataclass
@dataclass(frozen=True)
class Position:
 evidence_id:str; proposition:str; polarity:int; confidence:float
@dataclass(frozen=True)
class Conflict:
 proposition:str; left_id:str; right_id:str; severity:float
def conflicts(items:list[Position])->tuple[Conflict,...]:
 out=[]
 for i,a in enumerate(items):
  if a.polarity not in {-1,1} or not 0<=a.confidence<=1:raise ValueError("invalid evidence position")
  for b in items[i+1:]:
   if a.proposition==b.proposition and a.polarity!=b.polarity:
    out.append(Conflict(a.proposition,a.evidence_id,b.evidence_id,min(a.confidence,b.confidence)))
 return tuple(out)
