def render_metadata(ir, timeline):
    return {
      "scene_id":ir["scene_id"],
      "render_target":"1920x1080",
      "fps":30,
      "timing_mode":"AUDIO_DRIVEN",
      "duration_source":timeline["duration_source"],
      "audio_required":True,
      "asset_count":len(ir.get("assets",[])),
      "deterministic_keys":True
    }
