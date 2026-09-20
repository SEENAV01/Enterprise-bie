from hashlib import sha256
from bie.animation_intelligence.contracts import *
def ctx(**kw):
 d=dict(intent_id="ani",semantic_goal="teach",evidence_refs=("e",),reasoning_refs=("r",),
 visual_plan_fingerprint=sha256(b"vis").hexdigest(),cue=CueWindow("c",100,1100,2),visual_revision=1,target_profile="web")
 d.update(kw);return AnimationContext(**d)
def el(i="v",role="diagram",state="s1",visible=True,identity="x",geom="shape",payload=None):
 return VisualElementState(i,role,state,("e",),visible,True,identity,geom,payload or {})

import unittest
from bie.animation_intelligence.trace_selection import *
class T(unittest.TestCase):
 def test_process(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="process").action,"trace")
 def test_direction(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="process",direction_declared=False).status,"BLOCKED")
 def test_causal_block(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="causal").status,"BLOCKED")
 def test_causal(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="causal",causality_evidence=True).status,"PASS")
 def test_route(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="route",ordered_points=[(0,0),(1,1)]).status,"PASS")
 def test_route_review(self):self.assertEqual(select_trace(ctx(),target=el(),trace_kind="route",ordered_points=[(0,0)]).status,"REVIEW")
 def test_bad(self):
  with self.assertRaises(AnimationSemanticError):select_trace(ctx(),target=el(),trace_kind="random")
 def test_accept(self):self.assertFalse(select_trace(ctx(),target=el(),trace_kind="process").accepted)
