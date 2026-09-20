import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedTrack,UnifiedSceneIRDocument
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document,require_dsl_gate
class T(unittest.TestCase):
 def clean(self):
  e=UnifiedElement("e","text",{"text":"Hello"},("src",),("r",),{})
  t=UnifiedTrack("t","e","reveal",0,100,{},("src",),("r",))
  return UnifiedSceneIRDocument("s","1.0.0","Title",100,(e,),(t,),("src",),("r",))
 def test_pass(self):
  r=validate_scene_ir_document(self.clean());self.assertTrue(r.passed);self.assertEqual(len(r.validator_reports),7)
 def test_gate(self):self.assertTrue(require_dsl_gate(validate_scene_ir_document(self.clean())))
 def test_registry_block(self):
  d=self.clean().to_dict();d["tracks"][0]["action"]="explode";d.pop("fingerprint")
  r=validate_scene_ir_document(d);self.assertFalse(r.passed);self.assertTrue(any(x.startswith("REGISTRY:") for x in r.blockers))
 def test_decode_block(self):
  d=self.clean().to_dict();d["tracks"][0]["source_refs"]=[];d.pop("fingerprint")
  r=validate_scene_ir_document(d);self.assertFalse(r.passed);self.assertTrue(any(x.startswith("DECODE:") for x in r.blockers))
 def test_failed_gate(self):
  d=self.clean().to_dict();d["tracks"][0]["action"]="explode";d.pop("fingerprint")
  with self.assertRaises(ValueError):require_dsl_gate(validate_scene_ir_document(d))
 def test_not_accepted(self):self.assertFalse(validate_scene_ir_document(self.clean()).accepted)
