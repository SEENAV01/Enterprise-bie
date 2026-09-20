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
from bie.animation_intelligence.semantic_animation_intent import *
class T(unittest.TestCase):
 def test_pass(self): self.assertEqual(build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="introduce",preferred_actions=["enter"]).status,"PASS")
 def test_action(self): self.assertEqual(build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="focus",preferred_actions=["emphasize"]).action,"emphasize")
 def test_review(self): self.assertEqual(build_semantic_animation_intent(ctx(uncertainty=.5),target_ids=["v"],semantic_change="x").status,"REVIEW")
 def test_abstain(self): self.assertEqual(build_semantic_animation_intent(ctx(uncertainty=.9),target_ids=["v"],semantic_change="x").status,"ABSTAIN")
 def test_bad(self):
  with self.assertRaises(AnimationSemanticError): build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="x",preferred_actions=["dance"])
 def test_deterministic(self): self.assertEqual(build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="x").fingerprint,build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="x").fingerprint)
 def test_grounding(self): self.assertEqual(build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="x").evidence_refs,("e",))
 def test_not_accepted(self): self.assertFalse(build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="x").accepted)
