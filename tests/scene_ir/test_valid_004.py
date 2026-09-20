import unittest
from bie.scene_ir.temporal_validation import *
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(validate_temporal({"duration_ms":100,"tracks":[{"start_ms":0,"end_ms":100}]}).passed)
 def test_track_over(self):self.assertFalse(validate_temporal({"duration_ms":100,"tracks":[{"start_ms":0,"end_ms":101}]}).passed)
 def test_order(self):self.assertFalse(validate_temporal({"duration_ms":100,"tracks":[{"start_ms":50,"end_ms":50}]}).passed)
 def test_event(self):self.assertFalse(validate_temporal({"duration_ms":100,"events":[{"at_ms":101}]}).passed)
 def test_cue(self):self.assertFalse(validate_temporal({"duration_ms":100,"narration_cues":[{"start_ms":0,"end_ms":101}]}).passed)
 def test_not_accepted(self):self.assertFalse(validate_temporal({"duration_ms":100}).accepted)
