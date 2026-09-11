import unittest
from bie.reasoning.temporal_contradiction_witness import *

class T(unittest.TestCase):
    def test_cycle_witness(self):
        w=contradiction_witness([("a","b"),("b","c"),("c","a")])
        self.assertEqual(w[0],w[-1])
        self.assertGreaterEqual(len(w),4)
    def test_self_loop(self):
        self.assertEqual(contradiction_witness([("x","x")]),("x","x"))
    def test_consistent(self):
        self.assertEqual(contradiction_witness([("a","b"),("b","c")]),())
    def test_boolean(self):
        self.assertFalse(is_temporally_consistent([("a","b"),("b","a")]))
    def test_deterministic(self):
        self.assertEqual(contradiction_witness([("b","a"),("a","b")]),("a","b","a"))
