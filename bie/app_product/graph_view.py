from __future__ import annotations

import html
import math

from bie.knowledge_intelligence.knowledge_graph_validate import validate as validate_knowledge_graph
from bie.prerequisite_intelligence.graph import PrerequisiteGraph, roots, leaves
from bie.prerequisite_intelligence.teaching_order import teaching_order

from .contracts import GraphEdge, GraphNode, GraphView, GraphViewError


def _label(value: object, fallback: str) -> str:
    text = fallback if value is None else str(value).strip()
    if not text or len(text) > 512 or any(ord(c) < 32 for c in text):
        raise GraphViewError("invalid_graph_label")
    return text


def _confidence(value: object) -> float | None:
    if value is None:
        return None
    if type(value) not in {int, float} or isinstance(value, bool):
        raise GraphViewError("invalid_edge_confidence")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise GraphViewError("invalid_edge_confidence")
    return number


def concept_graph_view(graph: dict, *, max_nodes: int = 2048, max_edges: int = 8192) -> GraphView:
    if type(graph) is not dict:
        raise GraphViewError("concept_graph_dict_required")
    result = validate_knowledge_graph(graph)
    if not result["passed"]:
        raise GraphViewError("invalid_canonical_concept_graph")
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", ())
    if type(nodes) is not dict or type(edges) not in {list, tuple}:
        raise GraphViewError("invalid_concept_graph_shape")
    if not nodes or len(nodes) > max_nodes or len(edges) > max_edges:
        raise GraphViewError("concept_graph_resource_budget")
    node_rows = []
    for node_id in sorted(nodes):
        if type(node_id) is not str or not node_id or len(node_id) > 256:
            raise GraphViewError("invalid_concept_id")
        data = nodes[node_id]
        if type(data) is not dict:
            raise GraphViewError("invalid_concept_payload")
        node_rows.append(
            GraphNode(
                node_id,
                _label(data.get("label"), node_id),
                _label(data.get("node_type", "concept"), "concept"),
            )
        )
    edge_rows = []
    seen = set()
    for item in edges:
        if type(item) is not dict:
            raise GraphViewError("invalid_concept_edge")
        source = item.get("source")
        target = item.get("target")
        relation = item.get("type")
        if type(source) is not str or type(target) is not str or type(relation) is not str:
            raise GraphViewError("invalid_concept_edge")
        key = (source, target, relation)
        if key in seen:
            raise GraphViewError("duplicate_concept_edge")
        seen.add(key)
        edge_rows.append(GraphEdge(source, target, _label(relation, "relation"), _confidence(item.get("confidence"))))
    edge_rows.sort(key=lambda e: (e.source, e.target, e.relation))
    return GraphView("concept", tuple(node_rows), tuple(edge_rows))


def prerequisite_graph_view(
    graph: PrerequisiteGraph, *, max_nodes: int = 2048, max_edges: int = 8192
) -> GraphView:
    if type(graph) is not PrerequisiteGraph:
        raise GraphViewError("canonical_prerequisite_graph_required")
    if not graph.nodes or len(graph.nodes) > max_nodes:
        raise GraphViewError("prerequisite_graph_resource_budget")
    edge_pairs = []
    for source in sorted(graph.nodes):
        if source not in graph.outgoing or source not in graph.incoming:
            raise GraphViewError("incomplete_prerequisite_adjacency")
        for target in sorted(graph.outgoing[source]):
            if target not in graph.nodes or source not in graph.incoming.get(target, set()):
                raise GraphViewError("inconsistent_prerequisite_adjacency")
            edge_pairs.append((source, target))
    if len(edge_pairs) > max_edges:
        raise GraphViewError("prerequisite_graph_resource_budget")
    try:
        order = tuple(teaching_order(set(graph.nodes), edge_pairs))
    except ValueError as exc:
        raise GraphViewError("cyclic_prerequisite_graph") from exc
    root_set, leaf_set = set(roots(graph)), set(leaves(graph))
    node_rows = tuple(
        GraphNode(node, node, "concept", node in root_set, node in leaf_set)
        for node in sorted(graph.nodes)
    )
    edge_rows = tuple(GraphEdge(a, b, "PREREQUISITE", None) for a, b in sorted(edge_pairs))
    return GraphView("prerequisite", node_rows, edge_rows, order)


def render_graph_html(view: GraphView) -> str:
    title = "Concept graph" if view.graph_type == "concept" else "Prerequisite graph"
    nodes = "".join(
        f'<li data-node-id="{html.escape(n.node_id)}"><strong>{html.escape(n.label)}</strong>'
        f' <span>{html.escape(n.node_type)}</span></li>'
        for n in view.nodes
    )
    edges = "".join(
        f"<li>{html.escape(e.source)} → {html.escape(e.target)} "
        f"({html.escape(e.relation)})</li>"
        for e in view.edges
    )
    return (
        f'<section aria-label="{html.escape(title)}"><h2>{html.escape(title)}</h2>'
        f'<h3>Nodes</h3><ul>{nodes}</ul><h3>Relationships</h3><ul>{edges}</ul></section>'
    )
