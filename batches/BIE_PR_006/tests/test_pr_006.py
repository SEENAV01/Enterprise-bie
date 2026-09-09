import unittest
from app.bie.prerequisite_intelligence.graph import *
class T(unittest.TestCase):
 def test_build(self):
  g=build_graph(["a","b"],[Edge("a","b")]); self.assertEqual(roots(g),["a"]); self.assertEqual(leaves(g),["b"])
 def test_unknown(self):
  with self.assertRaises(ValueError): build_graph(["a"],[Edge("a","b")])
 def test_self(self):
  with self.assertRaises(ValueError): build_graph(["a"],[Edge("a","a")])
 def test_dedup(self):
  g=build_graph(["a","b"],[Edge("a","b"),Edge("a","b")]); self.assertEqual(len(g.outgoing["a"]),1)
if __name__=="__main__": unittest.main()
