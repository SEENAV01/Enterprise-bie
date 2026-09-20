import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.interaction_resolution import *
class T(unittest.TestCase):
 def doc(self,verified=True):
  ui=UnifiedElement("ui","text",{"text":"speed"},("s",),("r",));sim=UnifiedElement("sim","simulation",{"execution_class":"verified_observed_execution" if verified else "conceptual"},("s",),("r",))
  return UnifiedSceneIRDocument("s","1.0.0","T",100,(ui,sim),(),("s",),("r",),interaction_cues=({"cue_id":"c","at_ms":10,"interaction_id":"speed","target_ids":["ui"]},),interaction_bindings=({"binding_id":"b","interaction_id":"speed","event_type":"tap","target_ids":["ui"],"action":"set","handler_ref":"handler:set_speed"},),state_bindings=({"binding_id":"sb","state_path":"sim.speed","target_id":"ui","property_name":"text"},),simulation_controls=({"control_id":"ctl","simulation_element_id":"sim","control_type":"slider","state_path":"sim.speed","requires_verified_execution":True},),metadata={"handler_refs":["handler:set_speed"],"state_paths":["sim.speed"]})
 def test_pass(self):self.assertTrue(resolve_interactions(self.doc()).passed)
 def test_verified(self):self.assertIn("verified_execution_required:ctl",resolve_interactions(self.doc(False)).blockers)
 def test_state(self):
  d=self.doc().to_dict();d["metadata"]["state_paths"]=[];d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertFalse(resolve_interactions(decode_scene_ir(d)).passed)
 def test_unknown_target(self):
  d=self.doc().to_dict();d["interaction_bindings"][0]["target_ids"]=["x"];d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertFalse(resolve_interactions(decode_scene_ir(d)).passed)
 def test_not_accepted(self):self.assertFalse(resolve_interactions(self.doc()).accepted)
