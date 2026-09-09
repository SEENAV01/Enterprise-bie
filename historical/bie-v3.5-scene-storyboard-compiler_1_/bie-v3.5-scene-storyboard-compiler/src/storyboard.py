from scene_decomposer import compile_scenes
from visual_staging import stage_for_scene
from animation_planner import make_animation_events
from sync_planner import timing_contract

def build_storyboard(script_units):
    scenes=compile_scenes(script_units)
    for s in scenes:
        stage_for_scene(s)
        make_animation_events(s)
    return {
      "schema_version":"3.5",
      "scenes":scenes,
      "timing_contract":timing_contract(),
      "implementation_target":"REMOTION_SCENE_DSL",
      "status":"STORYBOARD_READY"
    }
