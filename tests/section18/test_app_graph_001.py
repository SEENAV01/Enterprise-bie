from __future__ import annotations

from bie.app_product.contracts import GraphViewError
from bie.app_product.graph_view import concept_graph_view, render_graph_html
from bie.knowledge_intelligence.knowledge_graph_build import build
from .support import AppProductCase


class ConceptGraphViewerTests(AppProductCase):
    def graph(self):
        return build(
            [
                {"concept_id": "charge", "label": "Electric charge", "node_type": "concept"},
                {"concept_id": "force", "label": "Coulomb force", "node_type": "law"},
            ],
            [{"source": "charge", "target": "force", "type": "SUPPORTS", "confidence": 0.9}],
        )

    def test_actual_canonical_graph_is_consumed(self):
        view = concept_graph_view(self.graph())
        self.assertEqual(view.graph_type, "concept")
        self.assertEqual([n.node_id for n in view.nodes], ["charge", "force"])

    def test_edges_are_preserved(self):
        edge = concept_graph_view(self.graph()).edges[0]
        self.assertEqual((edge.source, edge.target, edge.relation), ("charge", "force", "SUPPORTS"))

    def test_confidence_is_preserved(self):
        self.assertEqual(concept_graph_view(self.graph()).edges[0].confidence, 0.9)

    def test_dangling_edge_is_rejected(self):
        graph = self.graph()
        graph["edges"] = ({"source": "charge", "target": "missing", "type": "SUPPORTS"},)
        with self.assertRaises(GraphViewError):
            concept_graph_view(graph)

    def test_self_loop_is_rejected_by_canonical_validation(self):
        graph = self.graph()
        graph["edges"] = ({"source": "charge", "target": "charge", "type": "SELF"},)
        with self.assertRaises(GraphViewError):
            concept_graph_view(graph)

    def test_duplicate_edges_are_rejected(self):
        graph = self.graph()
        graph["edges"] = tuple(graph["edges"]) * 2
        with self.assertRaises(GraphViewError):
            concept_graph_view(graph)

    def test_invalid_confidence_rejected(self):
        graph = self.graph()
        graph["edges"] = ({"source": "charge", "target": "force", "type": "SUPPORTS", "confidence": 2},)
        with self.assertRaises(GraphViewError):
            concept_graph_view(graph)

    def test_resource_budget_enforced(self):
        with self.assertRaises(GraphViewError):
            concept_graph_view(self.graph(), max_nodes=1)

    def test_html_is_accessible_and_escaped(self):
        graph = build(
            [{"concept_id": "x", "label": "<script>x</script>", "node_type": "concept"}],
            [],
        )
        html = render_graph_html(concept_graph_view(graph))
        self.assertIn('aria-label="Concept graph"', html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_view_does_not_claim_acceptance(self):
        data = concept_graph_view(self.graph()).to_safe_dict()
        self.assertEqual(data["source_status"], "CANONICAL_TYPED_INPUT")
        self.assertNotIn("accepted", data)


if __name__ == "__main__":
    import unittest
    unittest.main()
