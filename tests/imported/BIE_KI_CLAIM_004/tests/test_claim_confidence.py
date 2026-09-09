import unittest
from bie.knowledge_intelligence.claim_confidence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(score(1,1,1)["status"],"ACCEPT")
  self.assertEqual(score(.7,.7,.7)["status"],"REVIEW")
  self.assertEqual(score(.2,.2,.2)["status"],"REJECT")
  with self.assertRaises(E):score(-1,1,1)
if __name__=='__main__':unittest.main()
