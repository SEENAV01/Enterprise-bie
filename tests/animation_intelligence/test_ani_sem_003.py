from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),
        visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from bie.animation_intelligence.emphasize_selection import *
class T(unittest.TestCase):
 def test_pass(self): self.assertEqual(select_emphasis(ctx(),element=el(),reason="important").action,"emphasize")
 def test_text(self): self.assertEqual(select_emphasis(ctx(),element=el(role="text"),reason="term").payload["mode"],"highlight")
 def test_quant(self): self.assertFalse(select_emphasis(ctx(),element=el(),reason="value",quantitative_semantics=True).payload["scale_allowed"])
 def test_scale(self): self.assertTrue(select_emphasis(ctx(),element=el(),reason="value",quantitative_semantics=True,allow_scale_emphasis=True).payload["scale_allowed"])
 def test_compete(self): self.assertEqual(select_emphasis(ctx(),element=el(),reason="x",competing_focus=True).status,"REVIEW")
 def test_effect(self): self.assertIn("without_changing",select_emphasis(ctx(),element=el(),reason="x").steps[0].semantic_effect)
 def test_grounding(self): self.assertEqual(select_emphasis(ctx(),element=el(),reason="x").reasoning_refs,("r",))
 def test_not_accepted(self): self.assertFalse(select_emphasis(ctx(),element=el(),reason="x").accepted)
