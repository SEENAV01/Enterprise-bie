from __future__ import annotations

from html import escape
from math import cos, pi, sin

from bie.knowledge_intelligence.knowledge_graph_query import query as canonical_query
from bie.knowledge_intelligence.knowledge_graph_validate import validate as canonical_validate

from .models import OperatorError

MAX_NODES = 5000
MAX_EDGES = 20000


def _label(node_id: str, payload: dict[str, object]) -> str:
    for key in ("label", "canonical_label", "name", "title"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return node_id


def _source_refs(payload: dict[str, object]) -> tuple[str, ...]:
    values = payload.get("source_refs", payload.get("evidence_refs", ()))
    if values is None:
        return ()
    if not isinstance(values, (list, tuple)):
        raise OperatorError("concept_source_refs_must_be_sequence")
    out = []
    for value in values:
        if isinstance(value, str) and value:
            out.append(value)
        elif isinstance(value, dict) and isinstance(value.get("artifact_id"), str):
            out.append(value["artifact_id"])
        else:
            raise OperatorError("invalid_concept_source_ref")
    return tuple(sorted(set(out)))


def concept_graph_view(
    graph: dict[str, object],
    *,
    label_filter: str | None = None,
    relation_type: str | None = None,
    min_confidence: float = 0.0,
) -> dict[str, object]:
    if not isinstance(graph, dict):
        raise OperatorError("concept_graph_must_be_mapping")
    validation = canonical_validate(graph)
    if not validation["passed"]:
        raise OperatorError("invalid_concept_graph")
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", ())
    if not isinstance(nodes, dict) or not isinstance(edges, (list, tuple)):
        raise OperatorError("invalid_concept_graph_shape")
    if len(nodes) > MAX_NODES or len(edges) > MAX_EDGES:
        raise OperatorError("concept_graph_too_large")
    if not isinstance(min_confidence, (int, float)) or not 0 <= float(min_confidence) <= 1:
        raise OperatorError("invalid_min_confidence")
    selected = canonical_query(
        graph,
        label=label_filter,
        relation_type=relation_type,
        min_confidence=float(min_confidence),
    )
    selected_nodes = set(selected["node_ids"]) if label_filter is not None else set(nodes)
    selected_edges = []
    for edge in selected["edges"]:
        if edge["source"] in selected_nodes and edge["target"] in selected_nodes:
            selected_edges.append({
                "source": edge["source"],
                "target": edge["target"],
                "type": edge.get("type"),
                "confidence": float(edge.get("confidence", 1.0)),
            })
    view_nodes = []
    for node_id in sorted(selected_nodes):
        payload = nodes[node_id]
        if not isinstance(payload, dict):
            raise OperatorError("concept_node_must_be_mapping")
        view_nodes.append({
            "id": node_id,
            "label": _label(node_id, payload),
            "source_refs": list(_source_refs(payload)),
            "confidence": payload.get("confidence"),
        })
    return {
        "schema_version": "bie.app.concept-graph-view/1",
        "node_count": len(view_nodes),
        "edge_count": len(selected_edges),
        "nodes": view_nodes,
        "edges": selected_edges,
        "filter": {
            "label": label_filter,
            "relation_type": relation_type,
            "min_confidence": float(min_confidence),
        },
        "validation": {"passed": True, "issues": []},
        "source_provenance_inferred": False,
    }


def render_concept_graph(view: dict[str, object]) -> str:
    nodes = list(view["nodes"])
    edges = list(view["edges"])
    positions: dict[str, tuple[float, float]] = {}
    count = max(1, len(nodes))
    for index, node in enumerate(nodes):
        angle = 2 * pi * index / count
        positions[str(node["id"])] = (300 + 220 * cos(angle), 260 + 200 * sin(angle))
    edge_svg = "".join(
        (
            f"<line x1='{positions[str(e['source'])][0]:.1f}' y1='{positions[str(e['source'])][1]:.1f}' "
            f"x2='{positions[str(e['target'])][0]:.1f}' y2='{positions[str(e['target'])][1]:.1f}' "
            "stroke='currentColor' stroke-width='1' opacity='0.45' />"
        )
        for e in edges
    )
    node_svg = "".join(
        (
            f"<g data-node-id='{escape(str(n['id']), quote=True)}'>"
            f"<circle cx='{positions[str(n['id'])][0]:.1f}' cy='{positions[str(n['id'])][1]:.1f}' r='22' "
            "fill='none' stroke='currentColor' stroke-width='2' />"
            f"<text x='{positions[str(n['id'])][0]:.1f}' y='{positions[str(n['id'])][1]+38:.1f}' "
            "text-anchor='middle'>"
            f"{escape(str(n['label']))}</text></g>"
        )
        for n in nodes
    )
    textual = "".join(
        f"<li><strong>{escape(str(n['label']))}</strong> "
        f"<code>{escape(str(n['id']))}</code>"
        + (
            " — evidence: " + ", ".join(escape(str(x)) for x in n["source_refs"])
            if n["source_refs"] else " — no source refs declared"
        )
        + "</li>"
        for n in nodes
    )
    return (
        "<section class='concept-graph-viewer' aria-labelledby='concept-graph-title'>"
        "<h2 id='concept-graph-title'>Concept graph</h2>"
        f"<p>{len(nodes)} concepts, {len(edges)} visible relationships.</p>"
        "<svg viewBox='0 0 600 520' role='img' aria-labelledby='concept-graph-svg-title'>"
        "<title id='concept-graph-svg-title'>Concept relationship graph</title>"
        f"{edge_svg}{node_svg}</svg>"
        "<h3>Accessible concept list</h3>"
        f"<ul>{textual}</ul>"
        "</section>"
    )
