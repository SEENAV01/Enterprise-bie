import unittest
from claim_graph_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("cl","c","CONCEPT","DEFINES",["p"],.9)["role"],"DEFINES")
  self.assertEqual(link("cl","r","RELATION","SUPPORTS",["p"],1)["target_type"],"RELATION")
  with self.assertRaises(E):link("cl","c","BAD","SUPPORTS",["p"],1)
  with self.assertRaises(E):link("cl","c","CONCEPT","SUPPORTS",[],1)
