import unittest
from knowledge_intelligence.applicability_conditions import *
class T(unittest.TestCase):
 def test_contract(self):
  r=make("coulomb","point charges at rest",["p"],.95);self.assertEqual(r["target_id"],"coulomb")
  self.assertIn("point charges",r["condition"])
  with self.assertRaises(E):make("c","",["p"],1)
  with self.assertRaises(E):make("c","x",[],1)
