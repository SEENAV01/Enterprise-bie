import unittest
from bie.knowledge_intelligence.relation_causes import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("heat","expansion",["p"],.9,"text order")["target"],"expansion")
  with self.assertRaises(E):edge("x","x",["p"],1,"e")
  with self.assertRaises(E):edge("x","y",[],1,"e")
  with self.assertRaises(E):edge("x","y",["p"],1,"")
if __name__=='__main__':unittest.main()
