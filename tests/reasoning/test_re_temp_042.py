import unittest
from bie.reasoning.temporal_dependency_invalidation import *
class T(unittest.TestCase):
 def test_transitive(self): self.assertEqual(invalidate_temporal_dependents(["a"],[("a","b"),("b","c")]),("b","c"))
 def test_branch(self): self.assertEqual(invalidate_temporal_dependents(["a"],[("a","b"),("a","c")]),("b","c"))
 def test_none(self): self.assertEqual(invalidate_temporal_dependents(["x"],[("a","b")]),())
 def test_cycle_safe(self): self.assertEqual(invalidate_temporal_dependents(["a"],[("a","b"),("b","a")]),("b",))
