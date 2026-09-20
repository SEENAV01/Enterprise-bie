import unittest
from bie.visual_intelligence.visual_plan_contract import STAGES
from bie.visual_intelligence.director_handoff_adoption import *
from bie.visual_intelligence.visual_orchestrator import *
def ctx():
 i=VisualIntent("i","diagram",("e",),("r",),{});h=DirectorHandoff("d",1,"book",1,1,(i,),(TimingCue("c","i",0,10,1),));return adopt(h,"book",1)
def execf(stage,status="PASS"):
 return lambda x:{"artifact_id":stage.lower(),"payload":{"stage":stage},"status":status}
def ready():
 o=VisualOrchestrator()
 for s in STAGES[1:]:o.register(s,execf(s))
 return o
class T(unittest.TestCase):
 def test_full(self): p,r=ready().run("run",ctx(),"web");self.assertEqual(tuple(x.stage for x in p.stages),STAGES);self.assertIsNone(r.blocked_stage)
 def test_raw_reject(self):
  with self.assertRaises(RawSourceRejected):ready().run("run",ctx(),"web",{"raw_pdf":b"x"})
 def test_block(self):
  o=VisualOrchestrator()
  for s in STAGES[1:]:o.register(s,execf(s,"BLOCKED" if s=="LAYOUT" else "PASS"))
  p,r=o.run("run",ctx(),"web");self.assertEqual(r.blocked_stage,"LAYOUT");self.assertEqual(tuple(x.stage for x in p.stages),("DIR_ADOPT","REP","GRAM"))
 def test_missing(self):
  with self.assertRaises(OrchestratorError):VisualOrchestrator().run("run",ctx(),"web")
