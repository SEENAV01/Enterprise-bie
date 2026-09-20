import unittest
from bie.scene_ir.interaction_cues import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(validate_interaction_cues([InteractionCue("c",10,"i1",("e",),"tap")],100,("i1",)),())
 def test_unknown(self):self.assertEqual(validate_interaction_cues([InteractionCue("c",10,"i2",("e",),"tap")],100,("i1",)),("unknown_interaction:c",))
 def test_out(self):self.assertEqual(validate_interaction_cues([InteractionCue("c",101,"i1",("e",),"tap")],100,("i1",)),("interaction_cue_outside_scene:c",))
 def test_mode(self):
  with self.assertRaises(TemporalIRError):InteractionCue("c",10,"i1",("e",),"swipe")
 def test_target(self):
  with self.assertRaises(TemporalIRError):InteractionCue("c",10,"i1",(),"tap")
