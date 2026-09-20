import unittest
from bie.scene_ir.unified_scene_ir_contract import *
class T(unittest.TestCase):
 def make(self):
  e=UnifiedElement("e","text",{"text":"Hello"},("s",),("r",))
  t=UnifiedTrack("t","e","reveal",0,100,{},("s",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","Title",100,(e,),(t,),("s",),("r",),
    layout={"boxes":[{"x":0,"y":0,"width":1,"height":1}]},
    events=({"event_id":"ev","at_ms":50},),
    narration_cues=({"cue_id":"n","start_ms":0,"end_ms":100},),
    interaction_bindings=({"binding_id":"b"},),
    state_bindings=({"binding_id":"sb"},),
    simulation_controls=({"control_id":"c"},),
    accessibility_metadata=({"element_id":"e"},),
    capability_requests=({"capability_id":"cap"},),
    planned_fallbacks=({"fallback_id":"fb"},))
 def test_integrated_fields(self):
  d=self.make()
  self.assertEqual(d.events[0]["event_id"],"ev")
  self.assertEqual(d.interaction_bindings[0]["binding_id"],"b")
 def test_fingerprint(self):self.assertEqual(len(self.make().fingerprint),64)
 def test_deep_immutable(self):
  d=self.make()
  with self.assertRaises(TypeError):d.elements[0].props["text"]="mutate"
 def test_unknown_track_element(self):
  e=UnifiedElement("e","text",{"text":"x"},("s",),("r",))
  t=UnifiedTrack("t","x","reveal",0,10,{},("s",),("r",))
  with self.assertRaises(UnifiedSceneIRError):UnifiedSceneIRDocument("s","1.0.0","x",10,(e,),(t,),("s",),("r",))
 def test_track_time(self):
  e=UnifiedElement("e","text",{"text":"x"},("s",),("r",))
  t=UnifiedTrack("t","e","reveal",0,11,{},("s",),("r",))
  with self.assertRaises(UnifiedSceneIRError):UnifiedSceneIRDocument("s","1.0.0","x",10,(e,),(t,),("s",),("r",))
 def test_not_accepted(self):self.assertFalse(self.make().accepted)
