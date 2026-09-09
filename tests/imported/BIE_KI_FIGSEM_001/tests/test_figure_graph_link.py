import unittest
from bie.knowledge_intelligence.figure_graph_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("f",["c"],["p"],.9)["target_ids"],("c",))
  self.assertEqual(link("f",["c","c"],["p"],1)["target_ids"],("c",))
  with self.assertRaises(E):link("",["c"],["p"],1)
  with self.assertRaises(E):link("f",[],["p"],1)
