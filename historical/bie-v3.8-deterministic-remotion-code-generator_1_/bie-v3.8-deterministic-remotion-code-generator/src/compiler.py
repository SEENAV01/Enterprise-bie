from ir import compile_ir
from key_stability import assign_stable_keys
from timeline import build_timeline
from codegen import generate_component
from render_metadata import render_metadata

def compile_scene(scene_dsl, alignment=None):
    ir=assign_stable_keys(compile_ir(scene_dsl,alignment))
    timeline=build_timeline(ir)
    return {
      "ir":ir,
      "timeline":timeline,
      "component_source":generate_component(ir),
      "render_metadata":render_metadata(ir,timeline)
    }
