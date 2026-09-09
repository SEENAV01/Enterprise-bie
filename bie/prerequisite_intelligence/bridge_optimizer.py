from dataclasses import dataclass
@dataclass(frozen=True)
class BridgeStep:
 concept:str; minutes:int
def optimize_bridge(missing:set[str], edges:list[tuple[str,str]], known:set[str], minutes:dict[str,int])->list[BridgeStep]:
 parents={}
 for a,b in edges: parents.setdefault(b,set()).add(a)
 needed=set(); visiting=set()
 def add(n):
  if n in needed:return
  if n in known:return
  if n in visiting: raise ValueError("bridge dependency cycle")
  visiting.add(n)
  for p in sorted(parents.get(n,set())): add(p)
  visiting.remove(n)
  needed.add(n)
 for m in sorted(missing): add(m)
 # topological order over only needed
 indeg={n:0 for n in needed};out={n:set() for n in needed}
 for a,b in edges:
  if a in needed and b in needed and b not in out[a]:out[a].add(b);indeg[b]+=1
 ready=sorted(n for n in needed if indeg[n]==0);order=[]
 while ready:
  n=ready.pop(0);order.append(n)
  for x in sorted(out[n]):
   indeg[x]-=1
   if indeg[x]==0:ready.append(x);ready.sort()
 if len(order)!=len(needed):raise ValueError("bridge dependency cycle")
 return [BridgeStep(n,max(1,minutes.get(n,4))) for n in order]
