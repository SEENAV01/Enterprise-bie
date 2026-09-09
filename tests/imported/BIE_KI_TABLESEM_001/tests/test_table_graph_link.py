import unittest
from table_graph_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("t",["c"],"p",.9)["target_ids"],("c",))
  self.assertEqual(link("t",["c","c"],"p",1)["target_ids"],("c",))
  with self.assertRaises(E):link("",["c"],"p",1)
  with self.assertRaises(E):link("t",[],"p",1)
