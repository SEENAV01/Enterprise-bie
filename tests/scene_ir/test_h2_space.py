import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.spatial_resolution import *
class T(unittest.TestCase):
 def doc(self):
  a=UnifiedElement("a","text",{"text":"A"},("s",),("r",),{},{"x":.6,"y":.1,"width":.2,"height":.2})
  b=UnifiedElement("b","text",{"text":"B"},("s",),("r",),{},{"x":.1,"y":.1,"width":.2,"height":.2})
  return UnifiedSceneIRDocument("s","1.0.0","T",100,(a,b),(),("s",),("r",),layout={"relative_constraints":[{"constraint_id":"c","subject_id":"a","relation":"left_of","reference_id":"b","gap":.05}]})
 def test_resolve(self):self.assertTrue(resolve_spatial_constraints(self.doc())[1].passed)
 def test_satisfy(self):
  d,_=resolve_spatial_constraints(self.doc());b={x["element_id"]:x for x in d.layout["boxes"]};self.assertLessEqual(b["a"]["x"]+b["a"]["width"]+.05,b["b"]["x"]+1e-6)
 def test_unknown(self):
  d=self.doc().to_dict();d["layout"]["relative_constraints"][0]["reference_id"]="x";d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertFalse(resolve_spatial_constraints(decode_scene_ir(d))[1].passed)
 def test_deterministic(self):self.assertEqual(resolve_spatial_constraints(self.doc())[0].fingerprint,resolve_spatial_constraints(self.doc())[0].fingerprint)
 def test_not_accepted(self):self.assertFalse(resolve_spatial_constraints(self.doc())[1].accepted)
