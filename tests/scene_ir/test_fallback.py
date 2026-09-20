import unittest
from bie.scene_ir.compiler_capability_declarations import *
from bie.scene_ir.planned_fallback_contract import *
class T(unittest.TestCase):
 def reg(self):
  r=CapabilityRegistry();r.register(CompilerCapability("cap:static","1",("graph","image"),(),("web",)));return r
 def fb(self,**kw):
  d=dict(fallback_id="f",element_id="e",missing_capability_id="cap:anim",fallback_capability_id="cap:static",fallback_action="static_graph",semantic_equivalence="degraded_but_safe",preserves_source_refs=True,preserves_reasoning_refs=True,preserves_accessibility=True);d.update(kw);return PlannedFallback(**d)
 def test_pass(self):self.assertEqual(validate_fallback(self.fb(),self.reg(),"web","graph")[0],())
 def test_apply(self):self.assertEqual(apply_fallback_or_fail(self.fb(),self.reg(),"web","graph")["fallback_action"],"static_graph")
 def test_source(self):self.assertIn("fallback_loses_source_refs",validate_fallback(self.fb(preserves_source_refs=False),self.reg(),"web","graph")[0])
 def test_access(self):self.assertIn("fallback_loses_accessibility",validate_fallback(self.fb(preserves_accessibility=False),self.reg(),"web","graph")[0])
 def test_unsupported(self):self.assertIn("fallback_capability_unsupported",validate_fallback(self.fb(fallback_capability_id="x"),self.reg(),"web","graph")[0])
 def test_illustrative(self):self.assertIn("fallback_is_illustrative_only",validate_fallback(self.fb(semantic_equivalence="illustrative_only"),self.reg(),"web","graph")[1])
 def test_fail(self):
  with self.assertRaises(SceneIRCapabilityError):apply_fallback_or_fail(self.fb(preserves_reasoning_refs=False),self.reg(),"web","graph")
