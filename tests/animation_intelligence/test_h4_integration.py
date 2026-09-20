import unittest,hashlib
from bie.animation_intelligence.ani_actual_e2e import run_vis_to_sceneir_ready
from bie.animation_intelligence.ani_realbook_harness import *
from bie.animation_intelligence.ani_computed_benchmark import *
from bie.animation_intelligence.ani_section_gate import *
H=hashlib.sha256(b"vis").hexdigest()
def V(action="reveal"):
 return {"handoff_id":"vh","plan_fingerprint":H,
 "primitives":[{"primitive_id":"v","source_refs":["s"],"reasoning_refs":["r"],"animation_action":action}],
 "assets":[],"timing":[{"start_ms":0,"end_ms":100}],"accessibility_ready":True,"target_profile":"web",
 "handoff_fingerprint":hashlib.sha256(b"h").hexdigest(),"current":True,
 "unsupported_capabilities":[],"planned_fallbacks":{}}
class T(unittest.TestCase):
 def test_actual_e2e_to_gate(self):
  e2e=run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web")
  self.assertEqual(e2e.status,"PASS")
  rb=RealBookFixture("physics:x","physics","REAL_BOOK","book://fixture","licensed_or_user_supplied","a"*64,True,("reveal",))
  rbr=evaluate_realbook_case(rb,("reveal",))
  self.assertEqual(rbr.status,"PASS")
  br=run_computed_benchmark([BenchmarkArtifact("c",("v",),("v",),(),(),(),0,.8,"NOT_RUN")])
  self.assertEqual(br.status,"PASS")
  gate=evaluate_ani_section_gate(AniSectionEvidence(True,38,20,True,True,True,True,True,False,False))
  self.assertEqual(gate.implementation_status,"IMPLEMENTATION_SCOPE_COMPLETE")
  self.assertEqual(gate.acceptance_status,"ACCEPTANCE_BLOCKED")
 def test_mutation_stale_vis(self):
  bad=V();bad["current"]=False
  with self.assertRaises(Exception):
   run_vis_to_sceneir_ready("r",bad,visual_revision=1,narration_revision=1,target_profile="web")
 def test_mutation_missing_lineage(self):
  bad=V();bad["primitives"][0]["source_refs"]=[]
  with self.assertRaises(Exception):
   run_vis_to_sceneir_ready("r",bad,visual_revision=1,narration_revision=1,target_profile="web")
 def test_mutation_realbook_expectation(self):
  rb=RealBookFixture("physics:x","physics","REAL_BOOK","book://fixture","licensed_or_user_supplied","a"*64,True,("trace",))
  self.assertEqual(evaluate_realbook_case(rb,("reveal",)).status,"BLOCKED")
 def test_mutation_benchmark_trace(self):
  br=run_computed_benchmark([BenchmarkArtifact("c",("v",),("v",),(),("missing",),(),0,.8,"NOT_RUN")])
  self.assertEqual(br.status,"BLOCKED")
 def test_truth_boundary_acceptance(self):
  gate=evaluate_ani_section_gate(AniSectionEvidence(True,38,20,True,True,True,True,True,False,False))
  self.assertFalse(gate.accepted)
