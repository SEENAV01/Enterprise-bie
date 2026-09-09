import unittest
from knowledge_intelligence.relation_derives import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("v=u+at","a=dv/dt",["p"],["integrate"],.9)["type"],"DERIVES_FROM")
  with self.assertRaises(E):edge("x","x",["p"],["s"],1)
  with self.assertRaises(E):edge("x","y",["p"],[],1)
  with self.assertRaises(E):edge("x","y",[],["s"],1)
if __name__=='__main__':unittest.main()
