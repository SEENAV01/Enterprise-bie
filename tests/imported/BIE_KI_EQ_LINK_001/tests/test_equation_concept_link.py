import unittest
from equation_concept_link import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(link("eq1",["force"],["p"],.9)["concept_ids"],("force",))
  self.assertEqual(link("eq1",["a","a"],["p"],1)["concept_ids"],("a",))
  with self.assertRaises(E):link("",["c"],["p"],1)
  with self.assertRaises(E):link("e",[],["p"],1)
