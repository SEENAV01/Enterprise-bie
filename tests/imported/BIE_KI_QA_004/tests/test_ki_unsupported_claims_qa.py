import unittest
from bie.knowledge_intelligence.ki_unsupported_claims_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate([{"claim_id":"c","anchor_ids":["p"],"confidence":.9}])["passed"])
  self.assertFalse(evaluate([{"claim_id":"c","anchor_ids":[],"confidence":1}])["passed"])
  self.assertEqual(evaluate([{"claim_id":"c","anchor_ids":["p"],"confidence":.2}])["low_confidence"],("c",))
  self.assertTrue(evaluate([])["passed"])
if __name__=='__main__':unittest.main()
