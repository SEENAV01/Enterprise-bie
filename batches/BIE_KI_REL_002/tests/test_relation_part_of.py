import unittest
from knowledge_intelligence.relation_part_of import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(edge("nucleus","cell",["p"],1)["type"],"PART_OF")
  with self.assertRaises(E):edge("x","x",["p"],1)
  with self.assertRaises(E):edge("x","y",[],1)
  with self.assertRaises(E):edge("x","y",["p"],-1)
if __name__=='__main__':unittest.main()
