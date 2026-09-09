from dataclasses import dataclass
@dataclass(frozen=True)
class ReadinessCheck:
 concept:str; ready:bool; mastered:tuple[str,...]; missing:tuple[str,...]; score:float
def check_readiness(concept:str, prerequisites:set[str], mastery:dict[str,float], threshold:float=.75)->ReadinessCheck:
 if not 0<=threshold<=1: raise ValueError("threshold must be in [0,1]")
 mastered=tuple(sorted(p for p in prerequisites if mastery.get(p,0)>=threshold))
 missing=tuple(sorted(prerequisites-set(mastered)))
 vals=[mastery.get(p,0) for p in prerequisites]
 score=1.0 if not vals else sum(vals)/len(vals)
 return ReadinessCheck(concept,not missing,mastered,missing,round(score,6))
