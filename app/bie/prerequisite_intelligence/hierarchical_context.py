from dataclasses import dataclass
@dataclass(frozen=True)
class ContextLayer:
 name:str; concepts:frozenset[str]; distance:int
@dataclass(frozen=True)
class ContextResolution:
 prerequisite:str; found_in:str|None; distance:int|None
def resolve_context(prerequisites:set[str], layers:list[ContextLayer])->list[ContextResolution]:
 ordered=sorted(layers,key=lambda x:(x.distance,x.name))
 out=[]
 for p in sorted(prerequisites):
  hit=next((l for l in ordered if p in l.concepts),None)
  out.append(ContextResolution(p,hit.name if hit else None,hit.distance if hit else None))
 return out
