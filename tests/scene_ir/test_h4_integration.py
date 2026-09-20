import unittest
from bie.scene_ir.dsl_actual_e2e import run_ani_to_compiler_ready
from bie.scene_ir.asset_contract import AssetRegistry
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry
from bie.scene_ir.dsl_computed_benchmark import DSLBenchmarkArtifact,run_dsl_benchmark
from bie.scene_ir.dsl_section_gate import DSLSectionEvidence,evaluate_dsl_section_gate
class T(unittest.TestCase):
 def chain(self):
  h={"handoff_id":"h","tracks":[{"track_id":"t","action":"reveal","target_ids":["e"],"start_ms":0,"end_ms":100,"source_refs":["src"],"reasoning_refs":["r"],"parameters":{}}]}
  c=[{"element_id":"e","element_type":"text","props":{"text":"Hello"},"source_refs":["src"],"reasoning_refs":["r"],"accessibility":{}}]
  return run_ani_to_compiler_ready(ani_handoff=h,scene_id="s",title="T",duration_ms=100,element_catalog=c,ani_revision=2,source_registry={"src":{"current":True,"confidence":.9,"evidence_hash":"a"*64}},reasoning_registry={"r":{"current":True,"confidence":.9,"evidence_hash":"b"*64}},asset_registry=AssetRegistry(),compiler_registry=CapabilityRegistry(),target_profile="web")
 def test_truth(self):
  d,h,e=self.chain();self.assertEqual(e.status,"PASS")
  b=run_dsl_benchmark([DSLBenchmarkArtifact("a",("text",),tuple(x.element_type for x in d.elements),("reveal",),tuple(x.action for x in d.tracks),(),True,True,True,h.compiler_ready)])
  self.assertEqual(b.status,"PASS")
  g=evaluate_dsl_section_gate(DSLSectionEvidence(True,51,20,True,True,h.compiler_ready,True,True,True,True,False,False,False))
  self.assertEqual(g.implementation_status,"IMPLEMENTATION_SCOPE_COMPLETE");self.assertEqual(g.acceptance_status,"ACCEPTANCE_BLOCKED");self.assertTrue(g.can_move_to_comp);self.assertFalse(g.accepted)
 def test_no_exec(self):
  _,h,e=self.chain();self.assertEqual((h.compile_status,h.render_status,e.compile_status,e.render_status),("NOT_RUN","NOT_RUN","NOT_RUN","NOT_RUN"))
