import unittest
from bie.reasoning.dependency_graph import dependencies
class T(unittest.TestCase):
 def test_direct(self):self.assertEqual(dependencies(["a","b"],[("a","b")],"b"),("a",))
 def test_transitive(self):self.assertEqual(dependencies(["a","b","c"],[("a","b"),("b","c")],"c"),("a","b"))
 def test_none(self):self.assertEqual(dependencies(["a"],[],"a"),())
 def test_unknown(self):
  with self.assertRaises(ValueError):dependencies(["a"],[],"x")
