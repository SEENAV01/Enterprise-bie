import unittest
from bie.reasoning.decision_graph import *
class T(unittest.TestCase):
 def test_build(self):self.assertEqual(build(["a","b"],[("a","b")]).edges,(("a","b"),))
 def test_dedupe(self):self.assertEqual(build(["a","a"],[]).nodes,("a",))
 def test_unknown(self):
  with self.assertRaises(ValueError):build(["a"],[("a","b")])
 def test_self(self):
  with self.assertRaises(ValueError):build(["a"],[("a","a")])
