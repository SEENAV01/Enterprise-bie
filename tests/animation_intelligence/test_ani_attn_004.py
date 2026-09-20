import unittest
from bie.animation_intelligence.attention_contracts import *
from bie.animation_intelligence.narration_attention_sync import *
def cue(i,s,e,rev=2):return AttentionWindow(i,("n",),s,e,.5,"narration",rev,False)
def att(i,s,e,rev=2,target="a"):return AttentionWindow(i,(target,),s,e,.9,"attention",rev,True)
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,1000)],attention_windows=[att("a",100,900)]).status,"PASS")
 def test_stale(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,1000)],attention_windows=[att("a",100,900,1)]).status,"BLOCKED")
 def test_unbound(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,100)],attention_windows=[att("a",200,300)]).status,"BLOCKED")
 def test_multi_cue_review(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c1",0,150),cue("c2",100,300)],attention_windows=[att("a",100,200)]).status,"REVIEW")
 def test_overlap_same_target_block(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,1000)],attention_windows=[att("a",100,500,target="x"),att("b",400,700,target="x")],allow_overlap_same_target=False).status,"BLOCKED")
 def test_empty(self):
  with self.assertRaises(AttentionError):sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[],attention_windows=[att("a",0,10)])
 def test_primary(self):self.assertEqual(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,1000)],attention_windows=[att("a",100,900)]).primary_target,"a")
 def test_not_accepted(self):self.assertFalse(sync_narration_attention(decision_id="d",narration_revision=2,cue_windows=[cue("c",0,1000)],attention_windows=[att("a",100,900)]).accepted)
