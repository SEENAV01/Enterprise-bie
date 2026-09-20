import unittest
from bie.animation_intelligence.economics_animation_grammar import *
def C(i,role="demand",pts=((1,9),(2,8))):return Curve(i,role,pts,("src",),("r",))
class T(unittest.TestCase):
 def test_shift(self):self.assertEqual(plan_curve_shift("p",C("d"),C("d2",pts=((1,10),(2,9))),driver="income").status,"PASS")
 def test_driver(self):self.assertEqual(plan_curve_shift("p",C("d"),C("d2"),driver="").status,"BLOCKED")
 def test_role(self):
  with self.assertRaises(EconomicsAnimationError):plan_curve_shift("p",C("d","demand"),C("s","supply"),driver="x")
 def test_equilibrium_review(self):self.assertEqual(plan_curve_shift("p",C("d"),C("d2"),driver="x",equilibrium_before=(1,1)).status,"REVIEW")
 def test_flow(self):self.assertEqual(plan_circular_flow("f",("households","firms"),({"from":"households","to":"firms","label":"labor"},),source_refs=("s",),reasoning_refs=("r",)).status,"PASS")
 def test_bad_flow(self):self.assertEqual(plan_circular_flow("f",("a","b"),({"from":"a","to":"z","label":"x"},),source_refs=("s",),reasoning_refs=("r",)).status,"BLOCKED")
 def test_curve_points(self):
  with self.assertRaises(EconomicsAnimationError):plan_curve_shift("p",Curve("d","demand",((1,1),),("s",),("r",)),C("d2"),driver="x")
 def test_not_accepted(self):self.assertFalse(plan_curve_shift("p",C("d"),C("d2"),driver="x").accepted)
