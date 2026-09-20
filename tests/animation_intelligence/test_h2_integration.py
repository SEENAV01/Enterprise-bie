import unittest,hashlib
from bie.animation_intelligence.animation_plan_contract import AnimationTrack
from bie.animation_intelligence.ani_trace_matrix import *
from bie.animation_intelligence.ani_replay_currentness import *
from bie.animation_intelligence.ani_accessibility import *
from bie.animation_intelligence.simulation_execution_receipt import *
from bie.animation_intelligence.animation_performance_budget import *
H=hashlib.sha256(b"x").hexdigest()
class T(unittest.TestCase):
 def test_end_to_end_trust_controls(self):
  t=AnimationTrack("t","camera",("v",),0,100,("s",),("r",),reduced_motion_variant="static_focus",payload={"camera_mode":"orbit"})
  a=enforce_animation_accessibility([t],AccessibilityPolicy(True,allow_orbit_camera=False))
  self.assertEqual(a.status,"PASS")
  tr=audit_trace([TrackTrace("t",("s",),("r",),("v",),"SEM",("q",),("scene-node",),True)])
  self.assertTrue(tr.passed)
  vv=VersionVector(1,1,1,"1.0","web")
  rr=make_replay_record("run",vv,"input","output",("vis",))
  self.assertTrue(assert_current(rr,vv,"input",("vis",)))
  sr=SimulationExecutionReceipt("sim","engine","1",H,7,H,H,True,True,True)
  self.assertEqual(classify_simulation_claim(sr),"VERIFIED_OBSERVED_EXECUTION")
  bd=evaluate_budget(AnimationComplexity(("t",),1,1,0,0,0,1,1000),AnimationBudget("web",20,35,1000,2,5_000_000))
  self.assertEqual(bd.action,"PASS")
 def test_truth_boundary(self):
  with self.assertRaises(SimulationReceiptError):
   validate_receipt(SimulationExecutionReceipt("sim","engine","1",H,7,H,H,True,False,True))
