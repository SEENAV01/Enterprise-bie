import unittest
from app.bie.math_intelligence.unit_qa import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(assess_units((1,0,-1,0,0,0,0),(1,0,-1,0,0,0,0)).passed)
 def test_mismatch(self): self.assertIn("dimension_mismatch",assess_units((1,0,0,0,0,0,0),(0,0,1,0,0,0,0)).failures)
 def test_declared(self): self.assertIn("unit_not_declared",assess_units((0,)*7,(0,)*7,False).failures)
 def test_bad(self):
  with self.assertRaises(ValueError):assess_units((1,),(1,))
if __name__=="__main__":unittest.main()
