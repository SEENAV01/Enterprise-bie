import unittest
from bie.scene_ir.ani_dsl_adopter import adopt_ani_handoff
from bie.scene_ir.unified_scene_ir_codec import roundtrip_scene_ir
from bie.scene_ir.scene_ir_registry import default_registry
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document
class T(unittest.TestCase):
 def chain(self):
  h={"handoff_id":"ani:h","tracks":[{"track_id":"t","action":"reveal","target_ids":["e"],"start_ms":0,"end_ms":100,"source_refs":["src"],"reasoning_refs":["r"],"parameters":{"opacity":[0,1]}}]}
  c=[{"element_id":"e","element_type":"text","props":{"text":"Hello"},"source_refs":["src"],"reasoning_refs":["r"],"accessibility":{}}]
  return adopt_ani_handoff(h,scene_id="s",title="T",duration_ms=100,element_catalog=c,ani_revision=4)
 def test_chain(self):
  d,r=self.chain();d2=roundtrip_scene_ir(d);default_registry().normalize_document(d2);g=validate_scene_ir_document(d2)
  self.assertTrue(g.passed);self.assertEqual(d2.fingerprint,r.dsl_fingerprint);self.assertFalse(g.accepted)
 def test_immutable(self):
  d,_=self.chain();before=d.fingerprint
  with self.assertRaises(TypeError):d.elements[0].props["text"]="changed"
  self.assertEqual(d.fingerprint,before)
