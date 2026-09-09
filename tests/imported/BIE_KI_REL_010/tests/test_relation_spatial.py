import unittest
from bie.knowledge_intelligence.relation_spatial import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("nucleus","cell","INSIDE",["p"],.9)["relation"],"INSIDE")
  with self.assertRaises(E):edge("x","x","NEAR",["p"],1)
  with self.assertRaises(E):edge("x","y","BAD",["p"],1)
  with self.assertRaises(E):edge("x","y","NEAR",[],1)
if __name__=='__main__':unittest.main()
