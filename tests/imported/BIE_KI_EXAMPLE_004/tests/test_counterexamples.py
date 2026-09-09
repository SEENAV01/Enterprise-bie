import unittest
from knowledge_intelligence.counterexamples import *
class T(unittest.TestCase):
 def test_contract(self):
  r=create("e","c","not all metals magnetic","p",.9);self.assertEqual(r["type"],"COUNTEREXAMPLE")
  self.assertEqual(r["concept_id"],"c")
  with self.assertRaises(E):create("e","c","","p",1)
  with self.assertRaises(E):create("e","c","x","p",2)
if __name__=='__main__':unittest.main()
