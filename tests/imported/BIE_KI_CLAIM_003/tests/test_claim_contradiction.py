import unittest
from bie.knowledge_intelligence.claim_contradiction import *
class T(unittest.TestCase):
 def test_contract(self):
  a={"claim_id":"a","subject":"x","predicate":"is","object":"hot"};b={**a,"claim_id":"b","object":"cold"}
  self.assertTrue(detect(a,b)["contradiction"])
  self.assertEqual(detect(a,b)["status"],"REVIEW")
  self.assertFalse(detect(a,{**a,"claim_id":"b"})["contradiction"])
  with self.assertRaises(E):detect({},b)
if __name__=='__main__':unittest.main()
