import unittest
from bie.math_intelligence.teachable_math import *
class T(unittest.TestCase):
 def test_new(self): self.assertTrue(plan_step("x=2",1,True,False).explain)
 def test_risk(self): self.assertIn("misconception",plan_step("x=2",1,False,True).reason)
 def test_routine(self): self.assertFalse(plan_step("x=2",1,False,False).explain)
 def test_bad(self):
  with self.assertRaises(ValueError):plan_step("",1,False,False)
if __name__=="__main__":unittest.main()
