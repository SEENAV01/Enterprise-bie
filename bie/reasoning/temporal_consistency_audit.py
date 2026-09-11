"""RE-TEMP-029 — Audit explicit before-relations for self loops and directed cycles."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ConsistencyAudit:
    consistent:bool
    issues:tuple[str,...]

def audit_before_relations(edges):
    es=tuple(edges)
    issues=[]
    graph={}
    for a,b in es:
        if a==b: issues.append(f"self_loop:{a}")
        graph.setdefault(a,set()).add(b)
        graph.setdefault(b,set())
    visiting=set(); done=set()
    def dfs(n):
        if n in visiting: return True
        if n in done: return False
        visiting.add(n)
        cyc=any(dfs(m) for m in graph[n])
        visiting.remove(n); done.add(n)
        return cyc
    if any(dfs(n) for n in sorted(graph) if n not in done):
        issues.append("directed_cycle")
    return ConsistencyAudit(not issues,tuple(sorted(set(issues))))
