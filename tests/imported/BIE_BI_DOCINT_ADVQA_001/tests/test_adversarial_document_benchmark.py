import unittest
from bie.document_intelligence.adversarial_document_benchmark import *
class T(unittest.TestCase):
 def test_contract(self):
  cases=[{"id":x,"category":x,"score":.95} for x in REQUIRED]
  self.assertTrue(evaluate(cases)["passed"])
  self.assertEqual(evaluate(cases)["count"],8)
  with self.assertRaises(E):evaluate(cases[:-1])
  bad=list(cases);bad[0]={**bad[0],"score":2}
  with self.assertRaises(E):evaluate(bad)
if __name__=='__main__':unittest.main()
