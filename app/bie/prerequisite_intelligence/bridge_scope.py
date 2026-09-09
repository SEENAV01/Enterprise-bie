from dataclasses import dataclass
@dataclass(frozen=True)
class BridgeItem:
 concept:str; depth:int; minutes:int
def plan_bridge_scope(missing:set[str], dependency_edges:list[tuple[str,str]], max_depth:int=2, minutes_per_concept:int=4)->list[BridgeItem]:
 if max_depth<0 or minutes_per_concept<1: raise ValueError("invalid planning limits")
 parents={}
 for a,b in dependency_edges: parents.setdefault(b,set()).add(a)
 depth={m:0 for m in missing}; frontier=list(sorted(missing))
 while frontier:
  n=frontier.pop(0); d=depth[n]
  if d>=max_depth: continue
  for p in sorted(parents.get(n,set())):
   nd=d+1
   if p not in depth or nd<depth[p]:
    depth[p]=nd; frontier.append(p)
 return [BridgeItem(n,d,minutes_per_concept) for n,d in sorted(depth.items(),key=lambda x:(-x[1],x[0]))]
