import unittest
from bie.reasoning.grounded_causal_graph import CausalEdge, build_grounded_causal_graph

class TestGroundedCausalGraph(unittest.TestCase):
    def test_requires_supporting_evidence(self):
        with self.assertRaises(ValueError):
            build_grounded_causal_graph(["a","b"],[CausalEdge("a","b")])

    def test_assumption_or_conflict_forces_review(self):
        g=build_grounded_causal_graph(["a","b"],[
            CausalEdge("a","b",("e1",),assumptions=("no hidden confounder",),confidence=.9)
        ])
        self.assertTrue(g.requires_review)

    def test_conservative_confidence(self):
        g=build_grounded_causal_graph(["a","b","c"],[
            CausalEdge("a","b",("e1",),confidence=.9),
            CausalEdge("b","c",("e2",),confidence=.6)
        ])
        self.assertEqual(g.confidence,.6)
