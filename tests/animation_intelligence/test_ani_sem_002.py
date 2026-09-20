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
from bie.animation_intelligence.enter_exit_selection import *
class T(unittest.TestCase):
 def test_enter(self): self.assertEqual(select_enter_exit(ctx(),element=el(visible=False),event="enter").action,"enter")
 def test_visible(self): self.assertEqual(select_enter_exit(ctx(),element=el(),event="enter").status,"UNSUPPORTED")
 def test_reenter(self): self.assertEqual(select_enter_exit(ctx(),element=el(),event="enter",reintroduced=True).action,"enter")
 def test_exit(self): self.assertEqual(select_enter_exit(ctx(),element=el(),event="exit",semantically_active_after=False).action,"exit")
 def test_block(self): self.assertEqual(select_enter_exit(ctx(),element=el(),event="exit").status,"BLOCKED")
 def test_bad(self):
  with self.assertRaises(AnimationSemanticError): select_enter_exit(ctx(),element=el(),event="blink")
 def test_timing(self): self.assertEqual(select_enter_exit(ctx(),element=el(visible=False),event="enter").steps[0].start_ms,100)
 def test_not_accepted(self): self.assertFalse(select_enter_exit(ctx(),element=el(visible=False),event="enter").accepted)
