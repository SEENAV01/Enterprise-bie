import unittest
from bie.knowledge_intelligence.concept_evidence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(bind("c",["a","a","b"])["evidence_count"],2)
  self.assertEqual(bind("c",["a"])["anchor_ids"],("a",))
  with self.assertRaises(E):bind("",["a"])
  with self.assertRaises(E):bind("c",[])
if __name__=='__main__':unittest.main()
