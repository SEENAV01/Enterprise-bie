import unittest
from book_intelligence.completeness_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(evaluate(3,[1,2,3])["passed"])
  self.assertEqual(evaluate(3,[1,3],.9)["missing"],(2,))
  self.assertFalse(evaluate(10,list(range(1,10)),.95)["passed"])
  with self.assertRaises(E):evaluate(0,[])
if __name__=="__main__":unittest.main()
