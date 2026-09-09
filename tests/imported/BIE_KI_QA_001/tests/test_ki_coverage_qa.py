import unittest
from knowledge_intelligence.ki_coverage_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate(["a"],["a"])["passed"])
  self.assertFalse(evaluate(["a","b"],["a"],["b"])["passed"])
  self.assertEqual(evaluate([],[])["coverage"],1)
  with self.assertRaises(E):evaluate(["a"],[],["x"])
if __name__=='__main__':unittest.main()
