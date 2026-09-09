import unittest
from knowledge_intelligence.relation_exemplifies import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("falling apple","gravity",["p"],.9)["type"],"EXEMPLIFIES")
  with self.assertRaises(E):edge("x","x",["p"],1)
  with self.assertRaises(E):edge("x","y",[],1)
  with self.assertRaises(E):edge("x","y",["p"],2)
if __name__=='__main__':unittest.main()
