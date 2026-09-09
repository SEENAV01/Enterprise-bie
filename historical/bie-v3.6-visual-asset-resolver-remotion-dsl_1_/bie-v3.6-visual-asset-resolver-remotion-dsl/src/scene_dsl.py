DSL_VERSION="1.0"

def scene_spec(scene, assets):
    return {
      "dsl_version":DSL_VERSION,
      "scene_id":scene["scene_id"],
      "objective":scene["objective"],
      "narration_unit_ids":scene["narration_unit_ids"],
      "evidence_ids":scene.get("evidence_ids",[]),
      "duration":{"mode":"AUDIO_DRIVEN"},
      "assets":assets,
      "layers":[],
      "events":scene.get("animation_events",[]),
      "camera":[],
      "transitions":[],
      "sync_anchors":scene.get("sync_anchors",[])
    }

def add_layer(spec, layer_type, props=None):
    spec["layers"].append({"type":layer_type,"props":props or {}})
    return spec
