from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
 visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from hashlib import sha256
from bie.animation_intelligence.semantic_animation_intent import build_semantic_animation_intent
from bie.animation_intelligence.enter_exit_selection import select_enter_exit
from bie.animation_intelligence.reveal_selection import select_reveal
from bie.animation_intelligence.trace_selection import select_trace
from bie.animation_intelligence.camera_movement import select_camera_movement
from bie.animation_intelligence.simulation_state_animation import select_simulation_state_animation
class T(unittest.TestCase):
 def test_intent_to_enter(self):
  a=build_semantic_animation_intent(ctx(),target_ids=["v"],semantic_change="introduce",preferred_actions=["enter"])
  b=select_enter_exit(ctx(),element=el(visible=False),event="enter");self.assertEqual((a.action,b.status),("enter","PASS"))
 def test_reveal_order(self):
  r=select_reveal(ctx(),elements=[el("a"),el("b")],dependency_order=["a","b"]);self.assertEqual([s.target_ids[0] for s in r.steps],["a","b"])
 def test_trace_camera(self):
  tr=select_trace(ctx(),target=el("r"),trace_kind="route",ordered_points=[(0,0),(1,1)])
  cam=select_camera_movement(ctx(),focus_target_ids=["r"],semantic_need="follow");self.assertEqual((tr.action,cam.action),("trace","camera"))
 def test_sim_truth_boundary(self):
  x=select_simulation_state_animation(ctx(),simulation_id="sim",model_fingerprint=sha256(b"m").hexdigest(),seed=7,parameters={},
   states=({"state_id":"a"},{"state_id":"b"}),transitions=({"transition_id":"t","from":"a","to":"b"},));self.assertEqual(x.status,"REVIEW")
 def test_cues(self):
  for d in (select_enter_exit(ctx(),element=el(visible=False),event="enter"),select_reveal(ctx(),elements=[el("a")],dependency_order=["a"])):
   for s in d.steps:self.assertTrue(100<=s.start_ms<s.end_ms<=1100)
