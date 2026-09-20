import unittest,hashlib
from bie.visual_intelligence.capability_handoff import *
from bie.visual_intelligence.complexity_budget import *
from bie.visual_intelligence.visual_e2e_harness import *
from bie.visual_intelligence.qa_trace_matrix import *
from bie.visual_intelligence.accessibility_integration import *
from bie.visual_intelligence.asset_lifecycle import *
from bie.visual_intelligence.replay_currentness import *
H=hashlib.sha256(b"x").hexdigest()
def ready_asset():
 a=AssetLifecycle("a");a=transition(a,"REUSE_CANDIDATE","src");a=transition(a,"ACQUIRED","acq",uri="file://a",content_sha256=H,provenance_refs=("e",));a=transition(a,"GROUNDING_CHECKED","g",grounding_score=.9);a=transition(a,"RIGHTS_VERIFIED","r",rights_status="source-permitted");a=transition(a,"QUALITY_VERIFIED","q",quality_score=.9);return transition(a,"READY","ready")
def parts():
 trace=audit_trace([TraceRow("v",True,("e",),("r",),"rep","g","l",None,"a",("qa",),True)])
 acc=integrate_accessibility([AccessibleVisualNode("v","diagram",font_px=20,alt_required=True,alt_mode="long_description")],contrast_results={"v":True})
 hand=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[PrimitiveRequirement("v","vector",True,("2d",),None,("e",),("r",))],assets=[AssetBinding("a","file://a",H,"source-permitted",("e",))],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web")
 comp=evaluate_budget(SceneComplexity(("v",),3,50,1000,10,1,0,0,0),BudgetProfile("web",20,35,1000000,2,1000))
 vec=VersionVector(1,1,"1.0.0","1.0.0","web");rep=make_replay_record("run",vec,"in","out",("d",))
 stages=[StageEvidence(s,True,"PASS",s.lower()) for s in CANONICAL_STAGES]
 return trace,acc,hand,comp,vec,rep,stages
class T(unittest.TestCase):
 def test_pass(self):
  tr,ac,h,c,v,r,s=parts();self.assertTrue(run_visual_e2e(run_id="run",stage_evidence=s,trace_audit=tr,accessibility_result=ac,asset_states=[ready_asset()],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",)).passed)
 def test_raw_reject(self):
  tr,ac,h,c,v,r,s=parts()
  with self.assertRaises(VisualE2EError):run_visual_e2e(run_id="run",stage_evidence=s,trace_audit=tr,accessibility_result=ac,asset_states=[ready_asset()],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",),raw_source_supplied=True)
 def test_stale_stage(self):
  tr,ac,h,c,v,r,s=parts();s[2]=StageEvidence(s[2].stage,False,"PASS","x");self.assertFalse(run_visual_e2e(run_id="run",stage_evidence=s,trace_audit=tr,accessibility_result=ac,asset_states=[ready_asset()],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",)).passed)
 def test_missing_stage(self):
  tr,ac,h,c,v,r,s=parts()
  with self.assertRaises(VisualE2EError):run_visual_e2e(run_id="run",stage_evidence=s[:-1],trace_audit=tr,accessibility_result=ac,asset_states=[ready_asset()],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",))
 def test_bad_asset(self):
  tr,ac,h,c,v,r,s=parts();bad=AssetLifecycle("bad");self.assertFalse(run_visual_e2e(run_id="run",stage_evidence=s,trace_audit=tr,accessibility_result=ac,asset_states=[bad],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",)).passed)
 def test_not_accepted(self):
  tr,ac,h,c,v,r,s=parts();x=run_visual_e2e(run_id="run",stage_evidence=s,trace_audit=tr,accessibility_result=ac,asset_states=[ready_asset()],handoff=h,complexity_decision=c,output_semantic_ids=["v"],replay_record=r,replay_vector=v,input_fingerprint="in",replay_dependency_ids=("d",));self.assertFalse(x.accepted)
