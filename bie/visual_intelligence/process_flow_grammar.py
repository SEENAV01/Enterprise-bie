from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, make_plan

PROCESS_FLOW_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.process_flow", version="1.0.0",
    domains=("*",), representations=("process_flow", "workflow", "cycle"),
    allowed_primitives=("process_node", "decision_node", "start_end", "connector", "label"),
    required_roles=("process_step",),
    semantic_constraints=("flow edges preserve declared direction", "cycles must be explicitly marked as feedback/loop", "branch labels remain explicit"),
    aliases=("process-flow",), tags=("process", "flow", "sequence"),
)


def plan_process_flow(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str]):
    elements = []
    node_ids = set()
    for node in nodes:
        nid = str(node.get("id", "")).strip()
        if not nid or nid in node_ids:
            raise GrammarValidationError("node ids must be non-blank and unique")
        node_ids.add(nid)
        kind = str(node.get("kind", "process")).strip().lower()
        if kind not in {"process", "decision", "start", "end"}:
            raise GrammarValidationError(f"unsupported node kind: {kind}")
        elements.append({
            "id": f"node:{nid}", "role": "process_step", "primitive": "decision_node" if kind == "decision" else ("start_end" if kind in {"start", "end"} else "process_node"),
            "label": str(node.get("label", nid)), "source_ids": list(node.get("source_ids", evidence_refs)), "payload": {"kind": kind},
        })
    if not elements:
        raise GrammarValidationError("at least one process node is required")
    relations = []
    adjacency: dict[str, list[str]] = defaultdict(list)
    non_loop_edges = []
    for i, edge in enumerate(edges):
        src, dst = str(edge.get("source", "")).strip(), str(edge.get("target", "")).strip()
        if src not in node_ids or dst not in node_ids:
            raise GrammarValidationError("edge references unknown node")
        kind = str(edge.get("kind", "next")).strip().lower()
        explicit_loop = kind in {"loop", "feedback"} or bool(edge.get("loop", False))
        if not explicit_loop:
            adjacency[src].append(dst)
            non_loop_edges.append((src, dst))
        relations.append({"id": f"flow:{i}:{src}:{dst}", "source": f"node:{src}", "target": f"node:{dst}", "kind": kind, "source_ids": list(edge.get("source_ids", evidence_refs)), "payload": {"branch": edge.get("branch"), "explicit_loop": explicit_loop}})
    indegree = {nid: 0 for nid in node_ids}
    for src, dst in non_loop_edges:
        indegree[dst] += 1
    queue = deque(sorted(nid for nid, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        current = queue.popleft(); visited += 1
        for nxt in adjacency[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0: queue.append(nxt)
    if visited != len(node_ids):
        raise GrammarValidationError("implicit cycle detected; mark loop/feedback edges explicitly")
    return make_plan(PROCESS_FLOW_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, relations=relations, constraints=PROCESS_FLOW_GRAMMAR.semantic_constraints)
