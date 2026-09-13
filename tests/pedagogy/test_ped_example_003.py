import unittest
from bie.pedagogy.worked_example_fading import fading_plan
class T(unittest.TestCase):
 def test_decreases(self):
  p=fading_plan(5,.4,4); self.assertTrue(all(p[i].support_fraction>=p[i+1].support_fraction for i in range(len(p)-1)))
 def test_mastery(self): self.assertLess(fading_plan(5,.9)[0].support_fraction,fading_plan(5,.2)[0].support_fraction)
