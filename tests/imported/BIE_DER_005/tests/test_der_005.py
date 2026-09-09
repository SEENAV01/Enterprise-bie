import unittest
from bie.math_intelligence.assumptions import *
class T(unittest.TestCase):
 def test_div(self): self.assertIn("!= 0",infer_assumptions("divide","x")[0].statement)
 def test_sqrt(self): self.assertIn(">= 0",infer_assumptions("sqrt","x")[0].statement)
 def test_none(self): self.assertEqual(infer_assumptions("add","x"),())
 def test_explicit(self): self.assertTrue(mark_explicit(infer_assumptions("log","x")[0]).explicit)
if __name__=="__main__":unittest.main()
