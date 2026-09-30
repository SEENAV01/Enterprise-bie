from __future__ import annotations

from batch001_support import OperatorCase

from bie.prerequisite_intelligence.graph import Edge, PrerequisiteGraph, build_graph
from bie.product_app_v1.models import OperatorError
from bie.product_app_v1.prerequisite_graph_viewer import (
    prerequisite_graph_view,
    render_prerequisite_graph,
)


class AppGraph002Tests(OperatorCase):
    def graph(self):
        return build_graph(
            {"charge", "force", "field", "potential"},
            [
                Edge("charge", "force"),
                Edge("charge", "field"),
                Edge("field", "potential"),
            ],
        )

    def test_view_preserves_prerequisite_edges(self):
        view = prerequisite_graph_view(self.graph())
        pairs = {(e["prerequisite"], e["dependent"]) for e in view["edges"]}
        self.assertEqual(pairs, {("charge", "force"), ("charge", "field"), ("field", "potential")})

    def test_view_reports_roots_and_leaves(self):
        view = prerequisite_graph_view(self.graph())
        self.assertEqual(view["roots"], ["charge"])
        self.assertEqual(view["leaves"], ["force", "potential"])

    def test_teaching_order_respects_dependencies(self):
        view = prerequisite_graph_view(self.graph())
        order = view["teaching_order"]
        self.assertLess(order.index("charge"), order.index("field"))
        self.assertLess(order.index("field"), order.index("potential"))

    def test_levels_are_dependency_aware(self):
        view = prerequisite_graph_view(self.graph())
        levels = {n["id"]: n["level"] for n in view["nodes"]}
        self.assertEqual(levels["charge"], 0)
        self.assertEqual(levels["field"], 1)
        self.assertEqual(levels["potential"], 2)

    def test_cycle_fails_closed(self):
        graph = PrerequisiteGraph(
            {"a", "b"},
            {"a": {"b"}, "b": {"a"}},
            {"a": {"b"}, "b": {"a"}},
        )
        with self.assertRaisesRegex(OperatorError, "prerequisite_graph_cycle"):
            prerequisite_graph_view(graph)

    def test_asymmetric_graph_fails_closed(self):
        graph = PrerequisiteGraph(
            {"a", "b"},
            {"a": {"b"}, "b": set()},
            {"a": set(), "b": set()},
        )
        with self.assertRaisesRegex(OperatorError, "prerequisite_graph_asymmetric"):
            prerequisite_graph_view(graph)

    def test_declared_labels_and_source_refs_are_preserved(self):
        view = prerequisite_graph_view(
            self.graph(),
            labels={"charge": "Electric charge"},
            source_refs={"charge": ["src:p1"]},
        )
        charge = next(n for n in view["nodes"] if n["id"] == "charge")
        self.assertEqual(charge["label"], "Electric charge")
        self.assertEqual(charge["source_refs"], ["src:p1"])
        self.assertFalse(view["source_provenance_inferred"])

    def test_invalid_source_refs_fail_closed(self):
        with self.assertRaises(OperatorError):
            prerequisite_graph_view(self.graph(), source_refs={"charge": [object()]})

    def test_html_has_svg_and_accessible_fallback(self):
        html = render_prerequisite_graph(prerequisite_graph_view(self.graph()))
        self.assertIn("role='img'", html)
        self.assertIn("Accessible prerequisite list", html)
        self.assertIn("Teaching order:", html)

    def test_html_escapes_labels(self):
        view = prerequisite_graph_view(self.graph(), labels={"charge": "<b>unsafe</b>"})
        html = render_prerequisite_graph(view)
        self.assertNotIn("<b>unsafe</b>", html)
        self.assertIn("&lt;b&gt;unsafe&lt;/b&gt;", html)


if __name__ == "__main__":
    import unittest
    unittest.main()
