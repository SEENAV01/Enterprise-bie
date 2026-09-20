import unittest
from bie.compiler.react_project_emitter import emit_react_project
from bie.compiler.root_emitter import emit_root
from bie.compiler.composition_emitter import emit_composition
from bie.compiler.scene_component_emitter import emit_scene_component
from bie.compiler.props_generation import emit_props
from bie.compiler.state_bindings_emitter import emit_state_bindings
from bie.compiler.reusable_primitives_emitter import emit_reusable_primitives
from bie.compiler.deterministic_codegen import plan_deterministic_codegen

class T(unittest.TestCase):
 def test_full_react_emitter_source_tree(self):
  files=list(emit_react_project(project_name="bie-video",remotion_version="4.0.0",react_version="19.0.0",typescript_version="5.9.0"))
  files += [
    emit_root(),
    emit_composition(composition_id="Lesson",width=1920,height=1080,fps=30,duration_in_frames=300,default_props={"topic":"Force"}),
    emit_scene_component(layers=({"layer_id":"title","component_name":"BieReveal","import_path":"./primitives","from_frame":0,"duration_in_frames":60,"props":{}},)),
    emit_props(fields=({"name":"topic","type":"string"},),defaults={"topic":"Force"}),
    emit_state_bindings(bindings=({"binding_id":"b","state_path":"sim.speed","target_id":"label","property_name":"text","transform":"number"},)),
    emit_reusable_primitives(),
  ]
  paths=[f.path for f in files]
  self.assertEqual(len(paths),len(set(paths)))
  self.assertIn("src/Root.tsx",paths)
  self.assertIn("src/Composition.tsx",paths)
  self.assertIn("src/Scene.tsx",paths)
  self.assertIn("src/primitives/index.tsx",paths)

  cg=plan_deterministic_codegen(
    scene_fingerprint="a"*64,
    compiler_version="1.0.0",
    deterministic_seed=42,
    component_snapshot=(("BieReveal","./primitives"),),
    files=[(f.path,f.content) for f in files],
  )
  self.assertEqual(len(cg.files),len(files))
  self.assertFalse(cg.accepted)

 def test_generated_animation_is_frame_driven(self):
  p=emit_reusable_primitives().content
  self.assertIn("useCurrentFrame()",p)
  self.assertIn("interpolate(",p)
  self.assertNotIn("transition:",p)
  self.assertNotIn("animation:",p)
