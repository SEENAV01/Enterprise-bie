
from typing import Dict,List
class CycleError(ValueError): pass
def find_cycles(tasks:Dict[str,dict])->List[List[str]]:
    cycles=[]; visiting=[]; seen=set()
    def dfs(n):
        if n in visiting:
            i=visiting.index(n); cyc=visiting[i:]+[n]
            canonical=min([tuple(cyc[j:-1]+cyc[:j]+[cyc[j]]) for j in range(len(cyc)-1)])
            if list(canonical) not in cycles: cycles.append(list(canonical))
            return
        if n in seen: return
        visiting.append(n)
        for d in tasks.get(n,{}).get("dependencies",[]):
            if d in tasks: dfs(d)
        visiting.pop(); seen.add(n)
    for n in sorted(tasks): dfs(n)
    return sorted(cycles)
def assert_acyclic(tasks):
    c=find_cycles(tasks)
    if c: raise CycleError(f"cycles detected: {c}")
    return True
