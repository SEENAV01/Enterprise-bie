import unittest
from bie.reasoning.graph_cycle_hardening import find_canonical_cycles, propose_cycle_breaks

class TestGraphCycleHardening(unittest.TestCase):
    def test_duplicate_cycle_witnesses_canonicalized(self):
        w=find_canonical_cycles(["a","b","c"],[("a","b"),("b","c"),("c","a")])
        self.assertEqual(len(w),1)
        self.assertEqual(w[0].nodes[0],w[0].nodes[-1])

    def test_unknown_node_rejected(self):
        with self.assertRaises(ValueError):
            find_canonical_cycles(["a"],[("a","b")])

    def test_break_proposal_is_deterministic(self):
        w=find_canonical_cycles(["a","b","c"],[("a","b"),("b","a"),("b","c"),("c","b")])
        self.assertEqual(propose_cycle_breaks(w),propose_cycle_breaks(reversed(w)))
