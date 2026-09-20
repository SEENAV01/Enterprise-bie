import unittest,hashlib
from bie.animation_intelligence.animation_plan_contract import *
H=hashlib.sha256(b"v").hexdigest()
class T(unittest.TestCase):
 def test_plan(self):
  t=AnimationTrack("t","reveal",("v",),0,100,("s",),("r",));p=AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",));self.assertTrue(p.plan_fingerprint)
 def test_duplicate(self):
  t=AnimationTrack("t","reveal",("v",),0,100,("s",),("r",))
  with self.assertRaises(AnimationPlanError):AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,t),0,100,("s",),("r",))
 def test_bounds(self):
  t=AnimationTrack("t","reveal",("v",),0,200,("s",),("r",))
  with self.assertRaises(AnimationPlanError):AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",))
 def test_schema(self):
  t=AnimationTrack("t","reveal",("v",),0,100,("s",),("r",))
  with self.assertRaises(AnimationPlanError):AnimationPlan("p","2.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",))
 def test_not_accepted(self):
  t=AnimationTrack("t","reveal",("v",),0,100,("s",),("r",));self.assertFalse(AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",)).accepted)
