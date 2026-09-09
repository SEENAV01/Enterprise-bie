import unittest
from app.bie.reasoning.causal_graph import *
class T(unittest.TestCase):
 def test_nodes(self):self.assertEqual(build_graph([CausalEdge("A","B","m",.9,"e")])[0],("A","B"))
 def test_empty(self):self.assertEqual(build_graph([]),((),()))
 def test_self(self):
  with self.assertRaises(ValueError):build_graph([CausalEdge("A","A","m",1,"e")])
 def test_conf(self):
  with self.assertRaises(ValueError):build_graph([CausalEdge("A","B","m",2,"e")])
