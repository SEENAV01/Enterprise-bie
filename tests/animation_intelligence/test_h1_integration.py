import unittest,hashlib
from bie.animation_intelligence.animation_plan_contract import *
from bie.animation_intelligence.global_timeline_solver import *
from bie.animation_intelligence.continuity_ledger import *
H=hashlib.sha256(b"v").hexdigest()
class T(unittest.TestCase):
 def test_plan_schedule_continuity(self):
  t=AnimationTrack("t","reveal",("v",),0,100,("s",),("r",))
  p=AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",))
  self.assertTrue(p.plan_fingerprint);self.assertTrue(solve([TrackRequest("t",0,100,0,100)]).solved)
  l=ContinuityLedger();self.assertTrue(l.add(ContinuityRecord("s","o","v","role",None,None,None)))
