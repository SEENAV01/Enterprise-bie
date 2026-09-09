import unittest
from bie.knowledge_intelligence.relation_contrasts import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("mass","weight",["p"],"meaning",.9)["type"],"CONTRASTS_WITH")
  self.assertEqual(edge("b","a",["p"],"d",1)["source"],"a")
  with self.assertRaises(E):edge("x","x",["p"],"d",1)
  with self.assertRaises(E):edge("x","y",["p"],"",1)
if __name__=='__main__':unittest.main()
