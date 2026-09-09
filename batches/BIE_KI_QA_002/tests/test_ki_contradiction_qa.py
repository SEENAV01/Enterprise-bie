import unittest
from knowledge_intelligence.ki_contradiction_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate([])["passed"])
  self.assertFalse(evaluate([{"status":"REVIEW","severity":"CRITICAL"}])["passed"])
  self.assertTrue(evaluate([{"status":"RESOLVED","severity":"CRITICAL"}])["passed"])
  self.assertTrue(evaluate([{"status":"REVIEW","severity":"LOW"}],1)["passed"])
if __name__=='__main__':unittest.main()
