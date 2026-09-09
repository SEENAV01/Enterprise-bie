import unittest,math
from app.bie.math_intelligence.numerical_qa import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(assess_numeric(2,2.000000001).passed)
 def test_fail(self): self.assertIn("outside_tolerance",assess_numeric(2,3).failures)
 def test_inf(self): self.assertIn("non_finite",assess_numeric(math.inf,math.inf).failures)
 def test_tol(self):
  with self.assertRaises(ValueError):assess_numeric(1,1,-1)
if __name__=="__main__":unittest.main()
