import unittest
from bie.compiler.text_compiler import compile_text_element
from bie.compiler.equation_compiler import compile_equation_element
from bie.compiler.vector_compiler import compile_vector_element
from bie.compiler.graph_compiler import compile_graph_element
from bie.compiler.chart_compiler import compile_chart_element
from bie.compiler.map_compiler import compile_map_element
from bie.compiler.timeline_compiler import compile_timeline_element
from bie.compiler.media_compiler import compile_image_or_video_element
from bie.compiler.simulation_compiler import compile_simulation_element
from bie.compiler.model2d_compiler import compile_model2d_element
from bie.compiler.model3d_compiler import compile_model3d_element
from bie.compiler.annotation_callout_compiler import compile_annotation_callout_element
from bie.compiler.particle_compiler import compile_particle_element
from bie.compiler.deterministic_codegen import plan_deterministic_codegen
from tests.compiler.h2_test_support import geo_props,sim_props

class T(unittest.TestCase):
 def test_compile_mixed_element_source_tree(self):
  base={"accessibility":{},"source_refs":["src"],"reasoning_refs":["r"]}
  elements=[
    (compile_text_element,{"element_id":"t","element_type":"text","props":{"text":"Hello"},**base}),
    (compile_equation_element,{"element_id":"eq","element_type":"equation","props":{"expression":"F=ma"},**base}),
    (compile_vector_element,{"element_id":"v","element_type":"vector","props":{"components":[1,2]},**base}),
    (compile_graph_element,{"element_id":"g","element_type":"graph","props":{"series":[{"points":[[0,0],[1,1]]}]},**base}),
    (compile_chart_element,{"element_id":"c","element_type":"chart","props":{"chart_kind":"bar","categories":["A"],"values":[1]},**base}),
    (compile_map_element,{"element_id":"m","element_type":"map","props":geo_props(),**base}),
    (compile_timeline_element,{"element_id":"tl","element_type":"timeline","props":{"events":[{"event_id":"a"},{"event_id":"b"}]},**base}),
    (compile_image_or_video_element,{"element_id":"i","element_type":"image","props":{"resolved_asset_path":"images/a.png"},**base}),
    (compile_simulation_element,{"element_id":"s","element_type":"simulation","props":sim_props(),**base}),
    (compile_model2d_element,{"element_id":"m2","element_type":"model2d","props":{"vertices":[[0,0],[1,1]],"edges":[[0,1]]},**base}),
    (compile_model3d_element,{"element_id":"m3","element_type":"model3d","props":{"resolved_asset_path":"models/a.glb"},**base}),
    (compile_annotation_callout_element,{"element_id":"a","element_type":"annotation","props":{"target_element_id":"t","text":"note"},**base}),
    (compile_particle_element,{"element_id":"p","element_type":"particle_system","props":{"particle_count":5},**base}),
  ]
  results=[fn(element) for fn,element in elements]
  self.assertEqual(len(results),13)
  self.assertEqual(len({r.source_path for r in results}),13)
  cg=plan_deterministic_codegen(
      scene_fingerprint="a"*64,
      compiler_version="1.0.0",
      deterministic_seed=7,
      component_snapshot=tuple(sorted((r.element_type,r.component_name) for r in results)),
      files=[(r.source_path,r.source_text) for r in results],
  )
  self.assertEqual(len(cg.files),13)
  self.assertFalse(cg.accepted)

 def test_asset_backed_compilers_do_not_allow_unresolved_asset_uri(self):
  base={"accessibility":{},"source_refs":["src"],"reasoning_refs":["r"]}
  with self.assertRaises(Exception):
   compile_image_or_video_element({"element_id":"i","element_type":"image","props":{"asset_ref":"asset://i"},**base})
  with self.assertRaises(Exception):
   compile_model3d_element({"element_id":"m","element_type":"model3d","props":{"asset_ref":"asset://m"},**base})
