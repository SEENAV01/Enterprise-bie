import unittest
from bie.visual_intelligence.visual_plan_contract import *
def r(stage): return StageRef(stage,stage.lower(),1,fp({"s":stage}),("e",),("r",))
class T(unittest.TestCase):
 def test_roundtrip(self):
  p=build_plan("p","1.0.0","1.0.0","s",1,"d",1,"web",[r("DIR_ADOPT")]); self.assertEqual(VisualPlan.from_dict(p.to_dict()).fingerprint,p.fingerprint)
 def test_order(self):
  with self.assertRaises(VisualPlanStageError): build_plan("p","1.0.0","1.0.0","s",1,"d",1,"web",[r("REP")])
 def test_append(self):
  p=build_plan("p","1.0.0","1.0.0","s",1,"d",1,"web",[r("DIR_ADOPT")]); self.assertEqual(append_stage(p,r("REP")).stages[-1].stage,"REP")
 def test_version(self):
  p=build_plan("p","1.2.0","2.0.0","s",1,"d",1,"web",[r("DIR_ADOPT")]); self.assertTrue(assert_compatible(p,1,2))
 def test_version_fail(self):
  p=build_plan("p","2.0.0","1.0.0","s",1,"d",1,"web",[r("DIR_ADOPT")])
  with self.assertRaises(VisualPlanVersionError): assert_compatible(p,1,1)
 def test_stale(self):
  x=StageRef("DIR_ADOPT","x",1,fp({"x":1}),("e",),("r",),False);p=build_plan("p","1.0.0","1.0.0","s",1,"d",1,"web",[x])
  with self.assertRaises(VisualPlanCurrentnessError): append_stage(p,r("REP"))
 def test_not_accepted(self): self.assertFalse(build_plan("p","1.0.0","1.0.0","s",1,"d",1,"web",[r("DIR_ADOPT")]).accepted)
