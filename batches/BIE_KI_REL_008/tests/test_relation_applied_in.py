import unittest
from knowledge_intelligence.relation_applied_in import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("refraction","lens design",["p"],.9)["type"],"APPLIED_IN")
  with self.assertRaises(E):edge("x","x",["p"],1)
  with self.assertRaises(E):edge("x","y",[],1)
  with self.assertRaises(E):edge("x","y",["p"],-1)
if __name__=='__main__':unittest.main()
