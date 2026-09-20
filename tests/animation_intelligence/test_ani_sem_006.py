from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
 visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from bie.animation_intelligence.morph_selection import *
class T(unittest.TestCase):
 def test_shape(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"p":"q"}).action,"morph")
 def test_empty(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={}).status,"BLOCKED")
 def test_duplicate(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"a":"x","b":"x"}).status,"BLOCKED")
 def test_eq_block(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"x":"x"},morph_kind="equation").status,"BLOCKED")
 def test_eq_pass(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"x":"x"},morph_kind="equation",semantic_equivalence=True).status,"PASS")
 def test_bad(self):
  with self.assertRaises(AnimationSemanticError):select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"x":"y"},morph_kind="liquid")
 def test_payload(self):self.assertEqual(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"x":"y"}).payload["correspondence"],{"x":"y"})
 def test_accept(self):self.assertFalse(select_morph(ctx(),source=el("a"),target=el("b"),correspondence={"x":"y"}).accepted)
