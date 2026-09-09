from dataclasses import dataclass
@dataclass(frozen=True)
class DecisionGraph: nodes:tuple[str,...]; edges:tuple[tuple[str,str],...]
def build(nodes,edges):
 ns=tuple(dict.fromkeys(nodes));known=set(ns)
 if any(a not in known or b not in known for a,b in edges):raise ValueError("unknown node")
 if any(a==b for a,b in edges):raise ValueError("self dependency")
 return DecisionGraph(ns,tuple(dict.fromkeys(edges)))
