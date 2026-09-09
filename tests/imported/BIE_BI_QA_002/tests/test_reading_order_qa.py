import unittest
from bie.document_intelligence.reading_order_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate(["a","b"],["a","b"])["passed"])
  self.assertFalse(evaluate(["a","b"],["a"])["passed"])
  self.assertFalse(evaluate(["a"],["a","x"])["passed"])
  self.assertTrue(evaluate(["a"],["a","a"])["duplicates"])
if __name__=="__main__":unittest.main()
