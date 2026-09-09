from dataclasses import dataclass
@dataclass(frozen=True)
class MasteryDependency:
 concept:str; ready:bool; blocking:tuple[str,...]; readiness:float
def evaluate_mastery(concept:str, prerequisites:set[str], mastery:dict[str,float], threshold:float=.75)->MasteryDependency:
 if not 0<=threshold<=1: raise ValueError("threshold must be in [0,1]")
 blocking=tuple(sorted(p for p in prerequisites if mastery.get(p,0)<threshold))
 vals=[mastery.get(p,0) for p in prerequisites]
 readiness=1.0 if not vals else sum(vals)/len(vals)
 return MasteryDependency(concept,not blocking,blocking,round(readiness,6))
