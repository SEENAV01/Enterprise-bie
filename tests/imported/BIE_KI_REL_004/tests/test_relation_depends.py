import unittest
from bie.knowledge_intelligence.relation_depends import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("acceleration","velocity",["p"],.9)["type"],"DEPENDS_ON")
  with self.assertRaises(E):edge("x","x",["p"],1)
  with self.assertRaises(E):edge("x","y",[],1)
  with self.assertRaises(E):edge("x","y",["p"],2)
if __name__=='__main__':unittest.main()
