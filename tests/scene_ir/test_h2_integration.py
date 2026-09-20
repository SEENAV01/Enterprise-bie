import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedTrack,UnifiedSceneIRDocument
from bie.scene_ir.spatial_resolution import resolve_spatial_constraints
from bie.scene_ir.temporal_resolution import resolve_temporal_consistency
from bie.scene_ir.interaction_resolution import resolve_interactions
from bie.scene_ir.accessibility_merge import merge_accessibility
from bie.scene_ir.compiler_capability_resolution import resolve_compiler_capabilities
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry,CompilerCapability
from bie.scene_ir.dsl_orchestrator import validate_scene_ir_document
class T(unittest.TestCase):
 def doc(self):
  ui=UnifiedElement("ui","text",{"text":"Speed"},("src",),("r",),{"keyboard_focusable":True},{"x":.1,"y":.1,"width":.25,"height":.2})
  sim=UnifiedElement("sim","simulation",{"execution_class":"verified_observed_execution"},("src",),("r",),{},{"x":.6,"y":.1,"width":.25,"height":.4})
  tr=(UnifiedTrack("tu","ui","reveal",0,200,{},("src",),("r",)),UnifiedTrack("ts","sim","simulation_state",100,900,{},("src",),("r",)))
  return UnifiedSceneIRDocument("scene","1.0.0","Integrated",1000,(ui,sim),tr,("src",),("r",),layout={"relative_constraints":[{"constraint_id":"c","subject_id":"ui","relation":"left_of","reference_id":"sim","gap":.05}]},events=({"event_id":"ev","at_ms":500,"target_ids":["sim"]},),narration_cues=({"cue_id":"n","start_ms":0,"end_ms":400,"target_ids":["ui"]},),interaction_cues=({"cue_id":"ic","at_ms":300,"interaction_id":"speed","target_ids":["ui"]},),interaction_bindings=({"binding_id":"b","interaction_id":"speed","event_type":"tap","target_ids":["ui"],"action":"set","handler_ref":"handler:set"},),state_bindings=({"binding_id":"sb","state_path":"sim.speed","target_id":"ui","property_name":"text"},),simulation_controls=({"control_id":"ctl","simulation_element_id":"sim","control_type":"slider","state_path":"sim.speed","requires_verified_execution":True},),accessibility_metadata=({"element_id":"ui","keyboard_focusable":True},{"element_id":"sim","reduced_motion_variant":"static_state","alt":"Simulation state"}),capability_requests=({"capability_id":"cap:text","element_id":"ui","element_type":"text","requested_action":"reveal","required":True},{"capability_id":"cap:sim","element_id":"sim","element_type":"simulation","requested_action":"simulation_state","required":True}),metadata={"handler_refs":["handler:set"],"state_paths":["sim.speed"],"element_lifetimes":[{"element_id":"ui","born_ms":0,"dead_ms":1000},{"element_id":"sim","born_ms":0,"dead_ms":1000}]})
 def test_chain(self):
  d=self.doc();d,s=resolve_spatial_constraints(d);self.assertTrue(s.passed);d,t=resolve_temporal_consistency(d);self.assertTrue(t.passed);self.assertTrue(resolve_interactions(d).passed);d,a=merge_accessibility(d);self.assertTrue(a.passed)
  reg=CapabilityRegistry();reg.register(CompilerCapability("cap:text","1",("text",),("reveal",),("web",)));reg.register(CompilerCapability("cap:sim","1",("simulation",),("simulation_state",),("web",)))
  self.assertTrue(resolve_compiler_capabilities(d,reg,"web").passed);self.assertTrue(validate_scene_ir_document(d).passed)
 def test_verified_guard(self):
  d=self.doc().to_dict();d["elements"][1]["props"]["execution_class"]="conceptual";d.pop("fingerprint")
  from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
  self.assertFalse(resolve_interactions(decode_scene_ir(d)).passed)
