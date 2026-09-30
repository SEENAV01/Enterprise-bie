from __future__ import annotations

from batch001_support import OperatorCase

from bie.knowledge_intelligence.knowledge_graph_build import build
from bie.product_app_v1.concept_graph_viewer import concept_graph_view, render_concept_graph
from bie.product_app_v1.models import OperatorError


class AppGraph001Tests(OperatorCase):
    def graph(self):
        return build(
            [
                {"concept_id": "force", "label": "Force", "source_refs": ["src:p1"]},
                {"concept_id": "acceleration", "label": "Acceleration", "source_refs": ["src:p2"]},
                {"concept_id": "mass", "label": "Mass", "source_refs": ["src:p3"]},
            ],
            [
                {"source": "force", "target": "acceleration", "type": "causes", "confidence": 0.95},
                {"source": "mass", "target": "acceleration", "type": "depends", "confidence": 0.80},
            ],
        )

    def test_view_uses_canonical_graph_shape(self):
        view = concept_graph_view(self.graph())
        self.assertEqual(view["node_count"], 3)
        self.assertEqual(view["edge_count"], 2)
        self.assertTrue(view["validation"]["passed"])

    def test_view_preserves_declared_source_refs(self):
        view = concept_graph_view(self.graph())
        node = next(x for x in view["nodes"] if x["id"] == "force")
        self.assertEqual(node["source_refs"], ["src:p1"])
        self.assertFalse(view["source_provenance_inferred"])

    def test_label_filter_uses_canonical_query(self):
        view = concept_graph_view(self.graph(), label_filter="Force")
        self.assertEqual([x["id"] for x in view["nodes"]], ["force"])

    def test_relation_filter_is_applied(self):
        view = concept_graph_view(self.graph(), relation_type="causes")
        self.assertEqual(len(view["edges"]), 1)
        self.assertEqual(view["edges"][0]["type"], "causes")

    def test_confidence_filter_is_applied(self):
        view = concept_graph_view(self.graph(), min_confidence=0.9)
        self.assertEqual(len(view["edges"]), 1)
        self.assertEqual(view["edges"][0]["source"], "force")

    def test_invalid_graph_fails_closed(self):
        graph = self.graph()
        graph["edges"] = graph["edges"] + ({"source": "force", "target": "missing", "type": "bad"},)
        with self.assertRaises(OperatorError):
            concept_graph_view(graph)

    def test_invalid_source_ref_fails_closed(self):
        graph = self.graph()
        graph["nodes"]["force"]["source_refs"] = [object()]
        with self.assertRaises(OperatorError):
            concept_graph_view(graph)

    def test_html_has_svg_and_accessible_text_fallback(self):
        html = render_concept_graph(concept_graph_view(self.graph()))
        self.assertIn("role='img'", html)
        self.assertIn("Accessible concept list", html)
        self.assertIn("src:p1", html)

    def test_html_escapes_untrusted_labels(self):
        graph = self.graph()
        graph["nodes"]["force"]["label"] = "<script>bad()</script>"
        html = render_concept_graph(concept_graph_view(graph))
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_view_does_not_invent_release_claims(self):
        view = concept_graph_view(self.graph())
        self.assertNotIn("accepted", view)
        self.assertNotIn("product_accepted", view)


if __name__ == "__main__":
    import unittest
    unittest.main()
