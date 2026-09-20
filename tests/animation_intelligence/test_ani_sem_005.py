from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
 visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from bie.animation_intelligence.transform_selection import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(select_transform(ctx(),source=el("a"),target=el("b",state="s2"),relation="change").action,"transform")
 def test_identity(self):self.assertEqual(select_transform(ctx(),source=el("a",identity="x"),target=el("b",state="s2",identity="y"),relation="x").status,"BLOCKED")
 def test_geometry(self):self.assertEqual(select_transform(ctx(),source=el("a"),target=el("b",state="s2",geom="graph"),relation="x").status,"REVIEW")
 def test_geometry_allowed(self):self.assertEqual(select_transform(ctx(payload={"geometry_conversion_allowed":True}),source=el("a"),target=el("b",state="s2",geom="graph"),relation="x").status,"PASS")
 def test_invariant(self):self.assertEqual(select_transform(ctx(),source=el("a"),target=el("b",state="s2"),relation="x",semantic_invariants=["mass"]).payload["invariants"],["mass"])
 def test_state(self):self.assertEqual(select_transform(ctx(),source=el("a"),target=el("b",state="s2"),relation="x").steps[0].target_state_id,"s2")
 def test_ground(self):self.assertEqual(select_transform(ctx(),source=el("a"),target=el("b",state="s2"),relation="x").evidence_refs,("e",))
 def test_accept(self):self.assertFalse(select_transform(ctx(),source=el("a"),target=el("b",state="s2"),relation="x").accepted)
