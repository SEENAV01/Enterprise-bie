from dataclasses import dataclass
@dataclass(frozen=True)
class Cluster:
 id:str; members:tuple[str,...]
def cluster_prerequisites(nodes:set[str], edges:list[tuple[str,str]], shared_threshold:int=1)->list[Cluster]:
 if shared_threshold<1: raise ValueError("shared_threshold >= 1")
 dependents={n:set() for n in nodes}
 for a,b in edges:
  if a not in nodes or b not in nodes: raise ValueError("unknown node")
  dependents[a].add(b)
 adj={n:set() for n in nodes}
 ordered=sorted(nodes)
 for i,a in enumerate(ordered):
  for b in ordered[i+1:]:
   if len(dependents[a]&dependents[b])>=shared_threshold: adj[a].add(b); adj[b].add(a)
 seen=set(); groups=[]
 for n in ordered:
  if n in seen: continue
  stack=[n]; comp=[]
  while stack:
   x=stack.pop()
   if x in seen: continue
   seen.add(x); comp.append(x); stack.extend(sorted(adj[x],reverse=True))
  groups.append(tuple(sorted(comp)))
 return [Cluster(f"cluster-{i+1:03d}",g) for i,g in enumerate(groups)]
