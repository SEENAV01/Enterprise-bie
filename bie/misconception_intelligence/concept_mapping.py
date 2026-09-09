from dataclasses import dataclass
@dataclass(frozen=True)
class Mapping:
 misconception:str; concept:str; score:float
def map_misconception(misconception:str, misconception_terms:set[str], concepts:dict[str,set[str]], threshold:float=.2)->list[Mapping]:
 out=[]
 for cid,terms in concepts.items():
  union=misconception_terms|terms
  score=len(misconception_terms&terms)/len(union) if union else 0
  if score>=threshold: out.append(Mapping(misconception,cid,round(score,6)))
 return sorted(out,key=lambda x:(-x.score,x.concept))
