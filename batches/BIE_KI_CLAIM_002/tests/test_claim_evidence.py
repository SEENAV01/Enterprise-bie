import unittest
from knowledge_intelligence.claim_evidence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(bind("c",["p"],.9)["grounded"])
  self.assertEqual(bind("c",["p","p"],1)["anchor_ids"],("p",))
  with self.assertRaises(E):bind("",["p"],1)
  with self.assertRaises(E):bind("c",[],1)
if __name__=='__main__':unittest.main()
