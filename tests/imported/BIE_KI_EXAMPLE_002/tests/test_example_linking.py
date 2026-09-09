import unittest
from knowledge_intelligence.example_linking import *
class T(unittest.TestCase):
 def test_contract(self):
  r=link("e",["c","c"],["p"],.9);self.assertEqual(r["concept_ids"],("c",))
  self.assertEqual(r["confidence"],.9)
  with self.assertRaises(E):link("e",[],["p"],1)
  with self.assertRaises(E):link("e",["c"],[],1)
if __name__=='__main__':unittest.main()
