import unittest
from bie.visual_intelligence.director_handoff_adoption import *
from bie.visual_intelligence.representation_grammar_arbitration import *
from bie.visual_intelligence.semantic_constraint_engine import *
from bie.visual_intelligence.visual_orchestrator import *
from bie.visual_intelligence.visual_plan_contract import STAGES
class T(unittest.TestCase):
 def test_spine(self):
  i=VisualIntent("i","vector",("e",),("r",),{});c=adopt(DirectorHandoff("d",1,"book",1,1,(i,),(TimingCue("c","i",0,100,1),)),"book",1)
  rep=RepDecision("rep",1,"physics","vector",.9,("e",),("r",),("arrow",))
  ar=arbitrate(rep,[Grammar("physics-vector","1.0.0",("physics",),("vector",),("arrow",))]);self.assertEqual(ar.status,"SELECTED")
  sr=evaluate({"metadata":{"reference_frame":"xy"}},["vectors require an explicit reference frame"]);self.assertTrue(sr.passed)
  o=VisualOrchestrator()
  for s in STAGES[1:]:o.register(s,lambda x,stage=s:{"artifact_id":stage.lower(),"payload":{"stage":stage}})
  p,r=o.run("run",c,"web");self.assertEqual(len(p.stages),8);self.assertTrue(p.current)
