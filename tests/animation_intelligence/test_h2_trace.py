import unittest
from bie.animation_intelligence.ani_trace_matrix import *
def R(**kw):
 d=dict(track_id="t",source_refs=("s",),reasoning_refs=("r",),visual_ids=("v",),owner_stage="SEM",qa_ids=("q",),downstream_node_ids=("n",),required=True);d.update(kw);return TrackTrace(**d)
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(audit_trace([R()]).passed)
 def test_source(self):self.assertFalse(audit_trace([R(source_refs=())]).passed)
 def test_reason(self):self.assertFalse(audit_trace([R(reasoning_refs=())]).passed)
 def test_visual(self):self.assertFalse(audit_trace([R(visual_ids=())]).passed)
 def test_qa(self):self.assertFalse(audit_trace([R(qa_ids=())]).passed)
 def test_downstream(self):self.assertFalse(audit_trace([R(downstream_node_ids=())]).passed)
 def test_duplicate(self):
  with self.assertRaises(AniTraceError):audit_trace([R(),R()])
 def test_not_accepted(self):self.assertFalse(audit_trace([R()]).accepted)
