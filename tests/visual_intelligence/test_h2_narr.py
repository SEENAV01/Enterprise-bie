import unittest
from bie.visual_intelligence.narration_sync import *
class T(unittest.TestCase):
 def test_bind(self):
  p=bind_visuals([Cue("c","i",0,100,2,"visual")],{"i":["v"]},2);self.assertEqual(p.bindings[0].visual_id,"v")
 def test_revision(self):
  with self.assertRaises(NarrationSyncError):bind_visuals([Cue("c","i",0,100,1,"visual")],{"i":["v"]},2)
 def test_unbound(self):self.assertIn("unbound_cue:c",bind_visuals([Cue("c","i",0,100,2,"visual")],{},2).warnings)
 def test_reveal_first(self):self.assertTrue(bind_visuals([Cue("c","i",0,100,2,"visual")],{"i":["a","b"]},2).bindings[0].reveal)
 def test_focus(self):self.assertTrue(bind_visuals([Cue("c","i",0,100,2,"equation")],{"i":["a"]},2).bindings[0].focus)
 def test_compete(self):
  p=bind_visuals([Cue("a","i",0,100,2,"visual"),Cue("b","j",50,150,2,"visual")],{"i":["x"],"j":["y"]},2);self.assertTrue(any(x.startswith("competing_focus") for x in p.warnings))
