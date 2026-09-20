import unittest,hashlib
from bie.animation_intelligence.animation_plan_contract import *
from bie.animation_intelligence.ani_sceneir_handoff import *
H=hashlib.sha256(b"v").hexdigest()
def P(action="reveal",fallback=None):
 t=AnimationTrack("t",action,("v",),0,100,("s",),("r",),reduced_motion_variant=fallback)
 return AnimationPlan("p","1.0.0","vh",H,1,1,"web",(t,),0,100,("s",),("r",))
class T(unittest.TestCase):
 def test_pass(self):self.assertFalse(build_sceneir_handoff(P()).blockers)
 def test_node(self):self.assertEqual(build_sceneir_handoff(P()).nodes[0].node_id,"ani:t")
 def test_unsupported(self):self.assertIn("unsupported_action:t",build_sceneir_handoff(P("explode")).blockers)
 def test_fallback(self):self.assertFalse(build_sceneir_handoff(P("explode","reveal")).blockers)
 def test_override(self):self.assertFalse(build_sceneir_handoff(P("explode"),capability_overrides={"explode":"reveal"}).blockers)
 def test_require(self):
  with self.assertRaises(SceneIRHandoffError):require_sceneir_ready(build_sceneir_handoff(P("explode")))
 def test_fp(self):self.assertEqual(build_sceneir_handoff(P()).animation_plan_fingerprint,P().plan_fingerprint)
 def test_not_accepted(self):self.assertFalse(build_sceneir_handoff(P()).accepted)
