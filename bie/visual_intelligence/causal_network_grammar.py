from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, make_plan

CAUSAL_NETWORK_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.causal_network", version="1.0.0",
    domains=("*",), representations=("causal_network", "causal_graph"),
    allowed_primitives=("cause_node", "effect_node", "mediator_node", "causal_arrow", "inhibitory_arrow", "feedback_arrow", "label"),
    required_roles=("causal_factor",),
    semantic_constraints=("causal arrows require evidence bindings", "association is not silently promoted to causation", "feedback cycles must be explicitly declared"),
    aliases=("causal-network",), tags=("causal", "mechanism", "network"),
)


def plan_causal_network(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str]):
    elements, ids = [], set()
    for node in nodes:
        nid = str(node.get("id", "")).strip()
        if not nid or nid in ids: raise GrammarValidationError("causal node ids must be non-blank and unique")
        ids.add(nid)
        role = str(node.get("role", "factor")).strip().lower()
        primitive = {"factor": "cause_node", "cause": "cause_node", "effect": "effect_node", "mediator": "mediator_node"}.get(role)
        if primitive is None: raise GrammarValidationError(f"unsupported causal role: {role}")
        elements.append({"id": f"cause:{nid}", "role": "causal_factor", "primitive": primitive, "label": str(node.get("label", nid)), "source_ids": list(node.get("source_ids", evidence_refs)), "payload": {"causal_role": role}})
    if not elements: raise GrammarValidationError("at least one causal node is required")
    relations = []
    adjacency = defaultdict(list); indegree = {nid: 0 for nid in ids}
    for i, edge in enumerate(edges):
        src, dst = str(edge.get("source", "")).strip(), str(edge.get("target", "")).strip()
        if src not in ids or dst not in ids or src == dst: raise GrammarValidationError("causal edge endpoints must be distinct known nodes")
        kind = str(edge.get("kind", "causes")).strip().lower()
        if kind not in {"causes", "inhibits", "mediates", "feedback", "associated"}: raise GrammarValidationError(f"unsupported causal edge kind: {kind}")
        evidence_kind = str(edge.get("evidence_kind", "causal")).strip().lower()
        if kind != "associated" and evidence_kind not in {"causal", "mechanistic", "experimental", "counterfactual"}:
            raise GrammarValidationError("causal edge lacks a causal evidence kind")
        explicit_feedback = kind == "feedback" or bool(edge.get("feedback", False))
        if not explicit_feedback and kind != "associated":
            adjacency[src].append(dst); indegree[dst] += 1
        relations.append({"id": f"causal:{i}:{src}:{dst}", "source": f"cause:{src}", "target": f"cause:{dst}", "kind": kind, "source_ids": list(edge.get("source_ids", evidence_refs)), "payload": {"evidence_kind": evidence_kind, "feedback": explicit_feedback}})
    queue = deque(sorted(n for n, d in indegree.items() if d == 0)); visited = 0
    while queue:
        cur = queue.popleft(); visited += 1
        for nxt in adjacency[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0: queue.append(nxt)
    if visited != len(ids): raise GrammarValidationError("causal cycle must be represented with explicit feedback edges")
    warnings = ["association edges are visually distinct and must not be narrated as causal"] if any(r["kind"] == "associated" for r in relations) else []
    return make_plan(CAUSAL_NETWORK_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, relations=relations, constraints=CAUSAL_NETWORK_GRAMMAR.semantic_constraints, warnings=warnings)
