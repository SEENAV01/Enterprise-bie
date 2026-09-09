from dataclasses import dataclass
@dataclass(frozen=True)
class Candidate:
 meaning:str; score:float; evidence:str
def disambiguate(symbol:str,context:str,candidates:dict[str,tuple[str,...]])->list[Candidate]:
 words=set((context or "").casefold().replace(","," ").replace("."," ").split());out=[]
 for meaning,hints in candidates.items():
  hits=[h for h in hints if h.casefold() in words]
  score=min(1.0,.35+.2*len(hits))
  out.append(Candidate(meaning,round(score,6),",".join(hits) or "symbol_only"))
 return sorted(out,key=lambda x:(-x.score,x.meaning))
