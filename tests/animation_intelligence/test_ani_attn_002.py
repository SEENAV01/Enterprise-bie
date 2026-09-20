import unittest
from bie.animation_intelligence.attention_contracts import *
from bie.animation_intelligence.focal_timing import *
def t():return AttentionTarget("a","equation",.9,("e",),("r",))
class T(unittest.TestCase):
 def test_window(self):self.assertEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).windows[0].target_ids,("a",))
 def test_lead(self):self.assertEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).windows[0].start_ms,880)
 def test_tail(self):self.assertEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).windows[0].end_ms,2080)
 def test_min(self):self.assertGreaterEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=100,cue_end_ms=150,narration_revision=2,min_focus_ms=500).windows[0].end_ms-plan_focal_timing(decision_id="d",target=t(),cue_start_ms=100,cue_end_ms=150,narration_revision=2,min_focus_ms=500).windows[0].start_ms,500)
 def test_bad_interval(self):
  with self.assertRaises(AttentionTimingError):plan_focal_timing(decision_id="d",target=t(),cue_start_ms=100,cue_end_ms=100,narration_revision=2)
 def test_priority(self):self.assertEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).windows[0].priority,.9)
 def test_grounding(self):self.assertEqual(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).evidence_refs,("e",))
 def test_not_accepted(self):self.assertFalse(plan_focal_timing(decision_id="d",target=t(),cue_start_ms=1000,cue_end_ms=2000,narration_revision=2).accepted)
