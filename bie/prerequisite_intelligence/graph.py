from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Edge:
    prerequisite: str
    dependent: str
    confidence: float = 1.0

@dataclass
class PrerequisiteGraph:
    nodes: set[str]
    outgoing: dict[str, set[str]]
    incoming: dict[str, set[str]]

def build_graph(nodes: Iterable[str], edges: Iterable[Edge]) -> PrerequisiteGraph:
    ns=set(nodes)
    outgoing={n:set() for n in ns}
    incoming={n:set() for n in ns}
    for e in edges:
        if e.prerequisite == e.dependent:
            raise ValueError("self-loop not allowed")
        if e.prerequisite not in ns or e.dependent not in ns:
            raise ValueError("edge references unknown node")
        outgoing[e.prerequisite].add(e.dependent)
        incoming[e.dependent].add(e.prerequisite)
    return PrerequisiteGraph(ns,outgoing,incoming)

def roots(g: PrerequisiteGraph) -> list[str]:
    return sorted(n for n in g.nodes if not g.incoming[n])

def leaves(g: PrerequisiteGraph) -> list[str]:
    return sorted(n for n in g.nodes if not g.outgoing[n])
