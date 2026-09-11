import unittest
from bie.reasoning.temporal_dependency_scheduler import *
class T(unittest.TestCase):
 def test_order(self): self.assertEqual(temporal_topological_order(["a","b","c"],[("a","b"),("b","c")]),("a","b","c"))
 def test_deterministic(self): self.assertEqual(temporal_topological_order(["b","a"],[]),("a","b"))
 def test_cycle(self):
  with self.assertRaises(ValueError): temporal_topological_order(["a","b"],[("a","b"),("b","a")])
 def test_unknown(self):
  with self.assertRaises(ValueError): temporal_topological_order(["a"],[("a","b")])
