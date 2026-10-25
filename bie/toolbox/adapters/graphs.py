"""Graphs laid out and traversed with NetworkX for BIE's D3 network block (Task 046a)."""
from __future__ import annotations

from .base import clean, need


def layout_and_bfs(edges: list, start, *, seed: int = 7, directed: bool = False) -> dict:
    """Node positions (0..1, a fixed seed so every render is the same) and the breadth-first visiting order from ``start``."""
    nx = need("networkx")
    graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_edges_from((a, b) for a, b in edges)
    if start not in graph:
        raise ValueError(f"start node {start!r} is not in the graph")
    pos = nx.kamada_kawai_layout(graph) if len(graph) <= 60 else nx.spring_layout(graph, seed=seed)
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0

    def norm(p):
        return [0.06 + 0.88 * (p[0] - min(xs)) / span, 0.06 + 0.88 * (p[1] - min(ys)) / span]
    order = [start] + [b for _, b in nx.bfs_edges(graph, start)]
    tree = [[a, b] for a, b in nx.bfs_edges(graph, start)]
    levels = nx.single_source_shortest_path_length(graph, start)
    return clean({"nodes": [{"id": str(n), "x": norm(pos[n])[0], "y": norm(pos[n])[1], "level": levels.get(n)} for n in graph.nodes],
                  "edges": [[str(a), str(b)] for a, b in graph.edges], "order": [str(n) for n in order],
                  "tree_edges": [[str(a), str(b)] for a, b in tree], "computed_by": f"networkx {nx.__version__} (kamada_kawai, bfs)"})
