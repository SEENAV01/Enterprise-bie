import unittest
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.compiler.semantic_easing_compiler import compile_semantic_easing_module
from bie.compiler.camera_compiler import compile_camera_track
from bie.compiler.equation_morph_compiler import compile_equation_morph
from bie.compiler.graph_transition_compiler import compile_graph_transition
from bie.compiler.deterministic_codegen import plan_deterministic_codegen

class T(unittest.TestCase):
 def test_animation_sources_join_deterministic_codegen(self):
  base={"source_refs":["src"],"reasoning_refs":["r"]}
  results=[
    compile_animation_track({"track_id":"reveal","element_id":"t","action":"reveal","start_ms":0,"end_ms":500,"parameters":{},**base}),
    compile_semantic_easing_module(["gentle","linear"]),
    compile_camera_track({"track_id":"cam","element_id":"scene","action":"camera","start_ms":0,"end_ms":500,"parameters":{"from":{"scale":1},"to":{"scale":1.2}},**base}),
    compile_equation_morph({"track_id":"eq","element_id":"eq","action":"morph","start_ms":0,"end_ms":500,"parameters":{"states":["x+x","2x"]},**base}),
    compile_graph_transition({"track_id":"g","element_id":"g","action":"transform","start_ms":0,"end_ms":500,"parameters":{"from_points":[[0,0],[1,1]],"to_points":[[0,1],[1,0]]},**base}),
  ]
  cg=plan_deterministic_codegen(
    scene_fingerprint="a"*64,
    compiler_version="1.0.0",
    deterministic_seed=11,
    component_snapshot=(("animation","v1"),),
    files=[(r.source_path,r.source_text) for r in results],
  )
  self.assertEqual(len(cg.files),5)
  self.assertFalse(cg.accepted)

 def test_generated_motion_avoids_css_animation_transition(self):
  base={"source_refs":["src"],"reasoning_refs":["r"]}
  sources=[
    compile_animation_track({"track_id":"reveal","element_id":"t","action":"reveal","start_ms":0,"end_ms":500,"parameters":{},**base}).source_text,
    compile_camera_track({"track_id":"cam","element_id":"scene","action":"camera","start_ms":0,"end_ms":500,"parameters":{"from":{"scale":1},"to":{"scale":1.2}},**base}).source_text,
  ]
  self.assertTrue(all("transition:" not in s and "animation:" not in s for s in sources))
