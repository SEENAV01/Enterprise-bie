from dataclasses import dataclass
@dataclass(frozen=True)
class AssumedKnowledge:
 concept:str; evidence:tuple[str,...]; confidence:float
def detect_assumed_knowledge(text:str, known_concepts:set[str])->list[AssumedKnowledge]:
 low=(text or "").casefold(); markers=("as you know","recall that","we know that","previously learned","familiar with")
 out=[]
 for c in sorted(known_concepts):
  cl=c.casefold(); ev=tuple(m for m in markers if m in low and cl in low[max(0,low.find(m)-80):low.find(m)+180])
  if ev: out.append(AssumedKnowledge(c,ev,min(1,.65+.1*len(ev))))
 return out
