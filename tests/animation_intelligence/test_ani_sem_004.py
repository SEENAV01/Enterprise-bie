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
from bie.animation_intelligence.reveal_selection import *
class T(unittest.TestCase):
 def test_progress(self): self.assertEqual(len(select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a","b"]).steps),2)
 def test_order(self): self.assertEqual(select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a","b"]).payload["order"],["a","b"])
 def test_group(self): self.assertEqual(len(select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a","b"],progressive=False).steps),1)
 def test_missing(self):
  with self.assertRaises(AnimationSemanticError): select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a"])
 def test_duplicate(self):
  with self.assertRaises(AnimationSemanticError): select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a","a"])
 def test_action(self): self.assertEqual(select_reveal(ctx(),elements=[el("a")],dependency_order=["a"]).action,"reveal")
 def test_cue(self): self.assertLessEqual(select_reveal(ctx(),elements=[el("a")],dependency_order=["a"]).steps[0].end_ms,1100)
 def test_not_accepted(self): self.assertFalse(select_reveal(ctx(),elements=[el("a")],dependency_order=["a"]).accepted)
