
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict, deque

ALLOWED_RELATIONS = {
    "IS_A","PART_OF","HAS_PART","REQUIRES","PREREQUISITE_OF",
    "CAUSES","CAUSE_OF","LEADS_TO","RESULTS_IN","DERIVED_FROM",
    "DEPENDS_ON","EXPLAINS","EXAMPLE_OF","COUNTEREXAMPLE_OF",
    "APPLIED_IN","USED_FOR","SUPPORTED_BY","EVIDENCED_BY",
    "CONTRASTS_WITH","GENERALIZES","SPECIALIZES","ENABLES",
    "LIMITED_BY","EXCEPTION_TO","PRECEDES","FOLLOWS","EXTENDS_TO"
}
SCOPES = {"BOOK_INTERNAL","BOOK_PREREQUISITE","EXTERNAL_EXTENSION",
          "EXTERNAL_APPLICATION","HIGHER_LEVEL","MODERN_DEVELOPMENT"}

@dataclass
class Node:
    id: str
    label: str
    scope: str = "BOOK_INTERNAL"
    kind: str = "concept"
    depth: int|None = None
    provenance: list[dict[str,Any]] = field(default_factory=list)

@dataclass
class Edge:
    source: str
    relation: str
    target: str
    confidence: float
    evidence: list[dict[str,Any]] = field(default_factory=list)

class M4Graph:
    def __init__(self):
        self.nodes: dict[str,Node] = {}
        self.edges: list[Edge] = []

    def add_node(self, n: Node):
        if n.scope not in SCOPES: raise ValueError("invalid scope")
        self.nodes[n.id] = n

    def add_edge(self, e: Edge):
        if e.relation not in ALLOWED_RELATIONS: raise ValueError("invalid relation")
        if e.source not in self.nodes or e.target not in self.nodes:
            raise ValueError("edge references unknown node")
        if not 0 <= e.confidence <= 1: raise ValueError("confidence must be 0..1")
        self.edges.append(e)

    def adjacency(self, relation=None):
        g=defaultdict(list)
        for e in self.edges:
            if relation is None or e.relation==relation: g[e.source].append(e.target)
        return g

    def cycles(self, relation="PREREQUISITE_OF"):
        g=self.adjacency(relation)
        color={}; out=[]
        def dfs(u,stack):
            color[u]=1; stack.append(u)
            for v in g.get(u,[]):
                if color.get(v,0)==1:
                    i=stack.index(v); out.append(stack[i:]+[v])
                elif color.get(v,0)==0: dfs(v,stack)
            stack.pop(); color[u]=2
        for n in self.nodes:
            if color.get(n,0)==0: dfs(n,[])
        return out

    def topological_learning_order(self):
        # Prerequisite edge A -> B means A must be learned before B.
        g=self.adjacency("PREREQUISITE_OF")
        indeg={n:0 for n in self.nodes}
        for u,vs in g.items():
            for v in vs: indeg[v]+=1
        q=deque(sorted([n for n,d in indeg.items() if d==0]))
        order=[]
        while q:
            u=q.popleft(); order.append(u)
            for v in sorted(g.get(u,[])):
                indeg[v]-=1
                if indeg[v]==0:q.append(v)
        if len(order)!=len(self.nodes):
            raise ValueError("Prerequisite graph contains a cycle")
        return order

    def frontier(self):
        f={"backward":[],"forward":[],"application":[]}
        for n in self.nodes.values():
            if n.scope=="BOOK_PREREQUISITE": f["backward"].append(n.id)
            elif n.scope in {"EXTERNAL_EXTENSION","HIGHER_LEVEL","MODERN_DEVELOPMENT"}: f["forward"].append(n.id)
            elif n.scope=="EXTERNAL_APPLICATION": f["application"].append(n.id)
        return f
