import unittest
from bie.scene_ir.dsl_actual_e2e import *
from bie.scene_ir.asset_contract import AssetRegistry
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry
class T(unittest.TestCase):
 def args(self):
  h={"handoff_id":"h","tracks":[{"track_id":"t","action":"reveal","target_ids":["e"],"start_ms":0,"end_ms":100,"source_refs":["src"],"reasoning_refs":["r"],"parameters":{}}]}
  c=[{"element_id":"e","element_type":"text","props":{"text":"Hello"},"source_refs":["src"],"reasoning_refs":["r"],"accessibility":{}}]
  return dict(ani_handoff=h,scene_id="s",title="T",duration_ms=100,element_catalog=c,ani_revision=2,source_registry={"src":{"current":True,"confidence":.9,"evidence_hash":"a"*64}},reasoning_registry={"r":{"current":True,"confidence":.9,"evidence_hash":"b"*64}},asset_registry=AssetRegistry(),compiler_registry=CapabilityRegistry(),target_profile="web")
 def test_pass(self):self.assertEqual(run_ani_to_compiler_ready(**self.args())[2].status,"PASS")
 def test_ready(self):self.assertTrue(run_ani_to_compiler_ready(**self.args())[1].compiler_ready)
 def test_no_execution(self):self.assertEqual(run_ani_to_compiler_ready(**self.args())[2].render_status,"NOT_RUN")
 def test_bad_prov(self):
  a=self.args();a["source_registry"]={};self.assertEqual(run_ani_to_compiler_ready(**a)[2].status,"BLOCK")
 def test_not_accepted(self):self.assertFalse(run_ani_to_compiler_ready(**self.args())[2].accepted)
