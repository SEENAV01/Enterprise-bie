import unittest
from book_intelligence.ocr_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate([.9,.95])["passed"])
  self.assertFalse(evaluate([.5,.9])["passed"])
  self.assertAlmostEqual(evaluate([.8,1])["mean"],.9)
  with self.assertRaises(E):evaluate([])
if __name__=="__main__":unittest.main()
