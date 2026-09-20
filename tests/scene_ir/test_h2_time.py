import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.temporal_resolution import *
class T(unittest.TestCase):
 def doc(self):
  e=UnifiedElement("e","text",{"text":"x"},("s",),("r",));t=UnifiedTrack("t","e","reveal",10,80,{},("s",),("r",))
  return UnifiedSceneIRDocument("s","1.0.0","T",100,(e,),(t,),("s",),("r",),events=({"event_id":"b","at_ms":80},{"event_id":"a","at_ms":20}),narration_cues=({"cue_id":"n","start_ms":0,"end_ms":90,"target_ids":["e"]},),interaction_cues=({"cue_id":"i","at_ms":50,"interaction_id":"tap","target_ids":["e"]},),metadata={"element_lifetimes":[{"element_id":"e","born_ms":0,"dead_ms":100}]})
 def test_pass(self):self.assertTrue(resolve_temporal_consistency(self.doc())[1].passed)
 def test_order(self):self.assertEqual(resolve_temporal_consistency(self.doc())[1].ordered_event_ids,("a","b"))
 def test_lifetime(self):
  d=self.doc().to_dict();d["metadata"]["element_lifetimes"][0]["dead_ms"]=50;d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertIn("track_outside_lifetime:t",resolve_temporal_consistency(decode_scene_ir(d))[1].blockers)
 def test_event(self):
  d=self.doc().to_dict();d["events"][0]["at_ms"]=101;d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertFalse(resolve_temporal_consistency(decode_scene_ir(d))[1].passed)
 def test_not_accepted(self):self.assertFalse(resolve_temporal_consistency(self.doc())[1].accepted)
