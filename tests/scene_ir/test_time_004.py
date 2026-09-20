import unittest
from bie.scene_ir.narration_cues import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(validate_narration_cues([NarrationCue("c",0,100,"txt:1",2)],100,2),())
 def test_stale(self):self.assertEqual(validate_narration_cues([NarrationCue("c",0,100,"txt:1",1)],100,2),("stale_narration_revision:c",))
 def test_over(self):self.assertEqual(validate_narration_cues([NarrationCue("c",0,101,"txt:1",2)],100,2),("cue_exceeds_scene:c",))
 def test_bad(self):
  with self.assertRaises(TemporalIRError):NarrationCue("c",10,10,"txt",1)
 def test_revision(self):
  with self.assertRaises(TemporalIRError):NarrationCue("c",0,10,"txt",0)
