from __future__ import annotations

from collections import deque
from html import escape

from bie.prerequisite_intelligence.graph import PrerequisiteGraph, leaves, roots

from .models import OperatorError

MAX_NODES = 5000
MAX_EDGES = 20000


def _validate_graph(graph: PrerequisiteGraph) -> tuple[list[str], list[tuple[str, str]]]:
    if not isinstance(graph, PrerequisiteGraph):
        raise OperatorError("invalid_prerequisite_graph_type")
    if len(graph.nodes) > MAX_NODES:
        raise OperatorError("prerequisite_graph_too_large")
    if set(graph.outgoing) != set(graph.nodes) or set(graph.incoming) != set(graph.nodes):
        raise OperatorError("prerequisite_graph_node_maps_mismatch")
    pairs: list[tuple[str, str]] = []
    for parent in sorted(graph.nodes):
        for child in sorted(graph.outgoing[parent]):
            if child not in graph.nodes or parent not in graph.incoming[child]:
                raise OperatorError("prerequisite_graph_asymmetric")
            pairs.append((parent, child))
    incoming_pairs = {
        (parent, child)
        for child in graph.nodes
        for parent in graph.incoming[child]
    }
    if incoming_pairs != set(pairs):
        raise OperatorError("prerequisite_graph_asymmetric")
    if len(pairs) > MAX_EDGES:
        raise OperatorError("prerequisite_graph_too_large")
    return sorted(graph.nodes), pairs


def _levels(graph: PrerequisiteGraph) -> tuple[dict[str, int], tuple[str, ...]]:
    indegree = {n: len(graph.incoming[n]) for n in graph.nodes}
    level = {n: 0 for n in graph.nodes}
    queue = deque(sorted(n for n, degree in indegree.items() if degree == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(graph.outgoing[node]):
            level[child] = max(level[child], level[node] + 1)
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(graph.nodes):
        raise OperatorError("prerequisite_graph_cycle")
    return level, tuple(order)


def prerequisite_graph_view(
    graph: PrerequisiteGraph,
    *,
    labels: dict[str, str] | None = None,
    source_refs: dict[str, list[str] | tuple[str, ...]] | None = None,
) -> dict[str, object]:
    nodes, pairs = _validate_graph(graph)
    levels, order = _levels(graph)
    labels = dict(labels or {})
    source_refs = dict(source_refs or {})
    view_nodes = []
    for node in nodes:
        refs = source_refs.get(node, ())
        if not isinstance(refs, (list, tuple)) or any(not isinstance(x, str) or not x for x in refs):
            raise OperatorError("invalid_prerequisite_source_refs")
        label = labels.get(node, node)
        if not isinstance(label, str) or not label.strip():
            raise OperatorError("invalid_prerequisite_label")
        view_nodes.append({
            "id": node,
            "label": label.strip(),
            "level": levels[node],
            "source_refs": sorted(set(refs)),
        })
    return {
        "schema_version": "bie.app.prerequisite-graph-view/1",
        "nodes": view_nodes,
        "edges": [{"prerequisite": a, "dependent": b} for a, b in pairs],
        "roots": roots(graph),
        "leaves": leaves(graph),
        "teaching_order": list(order),
        "node_count": len(nodes),
        "edge_count": len(pairs),
        "cycle_free": True,
        "source_provenance_inferred": False,
    }


def render_prerequisite_graph(view: dict[str, object]) -> str:
    nodes = list(view["nodes"])
    by_level: dict[int, list[dict[str, object]]] = {}
    for node in nodes:
        by_level.setdefault(int(node["level"]), []).append(node)
    positions: dict[str, tuple[int, int]] = {}
    for level in sorted(by_level):
        row = sorted(by_level[level], key=lambda n: str(n["id"]))
        for index, node in enumerate(row):
            x = 100 + index * 180
            y = 80 + level * 140
            positions[str(node["id"])] = (x, y)
    width = max([600] + [x + 100 for x, _ in positions.values()])
    height = max([300] + [y + 100 for _, y in positions.values()])
    edge_svg = "".join(
        (
            f"<line x1='{positions[str(e['prerequisite'])][0]}' y1='{positions[str(e['prerequisite'])][1]}' "
            f"x2='{positions[str(e['dependent'])][0]}' y2='{positions[str(e['dependent'])][1]}' "
            "stroke='currentColor' stroke-width='1.5' />"
        )
        for e in view["edges"]
    )
    node_svg = "".join(
        (
            f"<g data-node-id='{escape(str(n['id']), quote=True)}'>"
            f"<rect x='{positions[str(n['id'])][0]-55}' y='{positions[str(n['id'])][1]-25}' "
            "width='110' height='50' rx='8' fill='none' stroke='currentColor' stroke-width='2'/>"
            f"<text x='{positions[str(n['id'])][0]}' y='{positions[str(n['id'])][1]+4}' text-anchor='middle'>"
            f"{escape(str(n['label']))}</text></g>"
        )
        for n in nodes
    )
    order = " → ".join(escape(str(x)) for x in view["teaching_order"])
    details = "".join(
        f"<li><strong>{escape(str(n['label']))}</strong> (level {n['level']})"
        + (
            " — evidence: " + ", ".join(escape(str(x)) for x in n["source_refs"])
            if n["source_refs"] else " — no source refs declared"
        )
        + "</li>"
        for n in nodes
    )
    return (
        "<section class='prerequisite-graph-viewer' aria-labelledby='prerequisite-title'>"
        "<h2 id='prerequisite-title'>Prerequisite graph</h2>"
        f"<p>Teaching order: {order}</p>"
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-labelledby='prerequisite-svg-title'>"
        "<title id='prerequisite-svg-title'>Prerequisite dependency graph</title>"
        f"{edge_svg}{node_svg}</svg>"
        f"<h3>Accessible prerequisite list</h3><ul>{details}</ul>"
        "</section>"
    )
