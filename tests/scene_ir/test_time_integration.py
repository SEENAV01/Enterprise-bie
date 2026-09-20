import unittest
from bie.scene_ir.element_lifetime import *
from bie.scene_ir.animation_tracks import *
from bie.scene_ir.event_timeline import *
from bie.scene_ir.narration_cues import *
from bie.scene_ir.interaction_cues import *

class T(unittest.TestCase):
 def test_scene_temporal_contract(self):
  self.assertEqual(validate_lifetimes([ElementLifetime("e",0,500)],500),())
  self.assertEqual(validate_tracks([AnimationTrackSpec("t","e","reveal",0,300,"ease_out",{},("s",),("r",))],("e",),500),())
  events=build_event_timeline([TimelineEvent("ev",300,"state_change",("e",))],500)
  self.assertEqual(events[0].at_ms,300)
  self.assertEqual(validate_narration_cues([NarrationCue("n",0,300,"txt:1",2,("e",))],500,2),())
  self.assertEqual(validate_interaction_cues([InteractionCue("ic",350,"tap-1",("e",),"tap")],500,("tap-1",)),())
 def test_stale_narration_detected(self):
  self.assertIn("stale_narration_revision:n",validate_narration_cues([NarrationCue("n",0,100,"txt",1)],500,2))
