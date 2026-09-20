import unittest
from bie.animation_intelligence.attention_contracts import *
from bie.animation_intelligence.attention_model import build_attention_model
from bie.animation_intelligence.focal_timing import plan_focal_timing
from bie.animation_intelligence.competing_motion_prevention import prevent_competing_motion
from bie.animation_intelligence.narration_attention_sync import sync_narration_attention
class T(unittest.TestCase):
 def test_attention_pipeline(self):
  a=AttentionTarget("a","equation",.95,("e",),("r",),.1,.8)
  b=AttentionTarget("b","diagram",.6,("e",),("r",),.2,.4)
  model=build_attention_model([a,b]);self.assertEqual(model.primary_target,"a")
  focal=plan_focal_timing(decision_id="f",target=a,cue_start_ms=1000,cue_end_ms=1800,narration_revision=3)
  comp=prevent_competing_motion(decision_id="m",windows=focal.windows,motion_targets={"f:window":["a"]})
  self.assertEqual(comp.status,"PASS")
  cue=AttentionWindow("n",("n",),900,1900,.5,"narration",3,False)
  sync=sync_narration_attention(decision_id="s",narration_revision=3,cue_windows=[cue],attention_windows=focal.windows)
  self.assertEqual(sync.status,"PASS")
 def test_competing_motion_blocks(self):
  w1=AttentionWindow("w1",("a",),0,100,.9,"focus",1,True)
  w2=AttentionWindow("w2",("b",),50,150,.9,"focus",1,True)
  self.assertEqual(prevent_competing_motion(decision_id="x",windows=[w1,w2],motion_targets={"w1":["a"],"w2":["b"]}).status,"BLOCKED")
 def test_stale_sync_blocks(self):
  cue=AttentionWindow("c",("n",),0,1000,.5,"n",2,False)
  att=AttentionWindow("a",("v",),100,900,.9,"a",1,True)
  self.assertEqual(sync_narration_attention(decision_id="x",narration_revision=2,cue_windows=[cue],attention_windows=[att]).status,"BLOCKED")
 def test_no_self_acceptance(self):
  a=AttentionTarget("a","diagram",.9,("e",),("r",))
  self.assertFalse(build_attention_model([a]).accepted)
