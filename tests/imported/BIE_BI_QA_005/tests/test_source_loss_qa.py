import unittest
from bie.document_intelligence.source_loss_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate(["a"],["a"])["passed"])
  self.assertFalse(evaluate(["a","b"],["a"],["b"])["passed"])
  self.assertEqual(evaluate([],[])["coverage"],1.0)
  with self.assertRaises(E):evaluate(["a"],[],["x"])
if __name__=="__main__":unittest.main()
