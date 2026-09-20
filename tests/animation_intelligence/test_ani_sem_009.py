from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
 visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from bie.animation_intelligence.camera_movement import *
class T(unittest.TestCase):
 def test_pan(self):self.assertEqual(select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="follow").payload["mode"],"pan")
 def test_reduce(self):self.assertEqual(select_camera_movement(ctx(reduced_motion=True),focus_target_ids=["v"],semantic_need="focus",mode="zoom").payload["mode"],"static_focus")
 def test_orbit_review(self):self.assertEqual(select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="inspect",mode="orbit").status,"REVIEW")
 def test_orbit(self):self.assertEqual(select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="inspect",mode="orbit",depth_inspection=True).status,"PASS")
 def test_context(self):self.assertEqual(select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="inspect",mode="zoom",spatial_context_preserved=False).status,"BLOCKED")
 def test_bad(self):
  with self.assertRaises(AnimationSemanticError):select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="x",mode="spin")
 def test_targets(self):self.assertEqual(select_camera_movement(ctx(),focus_target_ids=["a","b"],semantic_need="x").steps[0].target_ids,("a","b"))
 def test_accept(self):self.assertFalse(select_camera_movement(ctx(),focus_target_ids=["v"],semantic_need="x").accepted)
