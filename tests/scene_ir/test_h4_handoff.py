import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.compiler_preflight_handoff import *
class R:
 def __init__(self,p=True,b=(),w=()):self.passed=p;self.blockers=b;self.warnings=w;self.resolved_assets=("asset:1",);self.supported_requests=("cap",);self.fallback_ids=();self.reading_order=("e",);self.keyboard_focus_order=()
class T(unittest.TestCase):
 def d(self):e=UnifiedElement("e","text",{"text":"x"},("s",),("r",));t=UnifiedTrack("t","e","reveal",0,10,{},("s",),("r",));return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(t,),("s",),("r",))
 def test_ready(self):self.assertTrue(build_compiler_preflight_handoff(self.d(),target_profile="web",provenance_receipt=R(),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R()).compiler_ready)
 def test_block(self):self.assertFalse(build_compiler_preflight_handoff(self.d(),target_profile="web",provenance_receipt=R(False,("x",)),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R()).compiler_ready)
 def test_no_execution(self):self.assertEqual(build_compiler_preflight_handoff(self.d(),target_profile="web",provenance_receipt=R(),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R()).compile_status,"NOT_RUN")
 def test_require(self):self.assertTrue(require_compiler_ready(build_compiler_preflight_handoff(self.d(),target_profile="web",provenance_receipt=R(),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R())))
 def test_id(self):
  a=dict(target_profile="web",provenance_receipt=R(),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R());self.assertEqual(build_compiler_preflight_handoff(self.d(),**a).handoff_id,build_compiler_preflight_handoff(self.d(),**a).handoff_id)
 def test_not_accepted(self):self.assertFalse(build_compiler_preflight_handoff(self.d(),target_profile="web",provenance_receipt=R(),asset_receipt=R(),integrity_receipt=R(),accessibility_receipt=R(),capability_receipt=R()).accepted)
