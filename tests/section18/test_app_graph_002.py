from __future__ import annotations

from bie.app_product.contracts import GraphViewError
from bie.app_product.graph_view import prerequisite_graph_view, render_graph_html
from bie.prerequisite_intelligence.graph import Edge, PrerequisiteGraph, build_graph
from .support import AppProductCase


class PrerequisiteGraphViewerTests(AppProductCase):
    def graph(self):
        return build_graph(
            {"algebra", "vectors", "coulomb"},
            (Edge("algebra", "coulomb"), Edge("vectors", "coulomb")),
        )

    def test_actual_canonical_prerequisite_graph_is_consumed(self):
        view = prerequisite_graph_view(self.graph())
        self.assertEqual(view.graph_type, "prerequisite")
        self.assertEqual({n.node_id for n in view.nodes}, {"algebra", "vectors", "coulomb"})

    def test_roots_and_leaf_are_exposed(self):
        view = prerequisite_graph_view(self.graph())
        rows = {n.node_id: n for n in view.nodes}
        self.assertTrue(rows["algebra"].is_root)
        self.assertTrue(rows["vectors"].is_root)
        self.assertTrue(rows["coulomb"].is_leaf)

    def test_edges_have_prerequisite_relation(self):
        view = prerequisite_graph_view(self.graph())
        self.assertTrue(view.edges)
        self.assertTrue(all(e.relation == "PREREQUISITE" for e in view.edges))

    def test_teaching_order_puts_prerequisites_first(self):
        order = prerequisite_graph_view(self.graph()).order
        self.assertLess(order.index("algebra"), order.index("coulomb"))
        self.assertLess(order.index("vectors"), order.index("coulomb"))

    def test_cycle_is_rejected(self):
        graph = build_graph({"a", "b"}, (Edge("a", "b"), Edge("b", "a")))
        with self.assertRaises(GraphViewError):
            prerequisite_graph_view(graph)

    def test_inconsistent_adjacency_is_rejected(self):
        graph = PrerequisiteGraph({"a", "b"}, {"a": {"b"}, "b": set()}, {"a": set(), "b": set()})
        with self.assertRaises(GraphViewError):
            prerequisite_graph_view(graph)

    def test_noncanonical_type_is_rejected(self):
        with self.assertRaises(GraphViewError):
            prerequisite_graph_view({"nodes": ["a"]})

    def test_resource_budget_enforced(self):
        with self.assertRaises(GraphViewError):
            prerequisite_graph_view(self.graph(), max_nodes=2)

    def test_html_has_accessible_prerequisite_label(self):
        html = render_graph_html(prerequisite_graph_view(self.graph()))
        self.assertIn('aria-label="Prerequisite graph"', html)
        self.assertIn("algebra", html)
        self.assertIn("coulomb", html)

    def test_output_is_deterministic(self):
        first = prerequisite_graph_view(self.graph()).to_safe_dict()
        second = prerequisite_graph_view(self.graph()).to_safe_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    import unittest
    unittest.main()
