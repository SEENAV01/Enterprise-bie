
from typing import Dict,List
class DependencyError(ValueError): pass
def missing_dependencies(tasks:Dict[str,dict])->Dict[str,List[str]]:
    out={}
    for tid,t in tasks.items():
        miss=[d for d in t.get("dependencies",[]) if d not in tasks]
        if miss: out[tid]=miss
    return out
def dependents(tasks:Dict[str,dict])->Dict[str,List[str]]:
    out={k:[] for k in tasks}
    for tid,t in tasks.items():
        for d in t.get("dependencies",[]):
            if d in out: out[d].append(tid)
    for k in out: out[k].sort()
    return out
def transitive_dependencies(tasks:Dict[str,dict],task_id:str)->List[str]:
    if task_id not in tasks: raise DependencyError("unknown task")
    seen=set(); stack=list(tasks[task_id].get("dependencies",[]))
    while stack:
        x=stack.pop()
        if x in seen: continue
        if x not in tasks: raise DependencyError(f"missing dependency {x}")
        seen.add(x); stack.extend(tasks[x].get("dependencies",[]))
    return sorted(seen)
def topo_order(tasks:Dict[str,dict])->List[str]:
    miss=missing_dependencies(tasks)
    if miss: raise DependencyError(f"missing dependencies: {miss}")
    indeg={k:0 for k in tasks}; dep=dependents(tasks)
    for k,t in tasks.items(): indeg[k]=len(t.get("dependencies",[]))
    ready=sorted([k for k,v in indeg.items() if v==0]); order=[]
    while ready:
        n=ready.pop(0); order.append(n)
        for x in dep[n]:
            indeg[x]-=1
            if indeg[x]==0: ready.append(x); ready.sort()
    if len(order)!=len(tasks): raise DependencyError("dependency cycle")
    return order
