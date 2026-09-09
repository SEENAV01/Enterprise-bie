def compile_ir(scene_dsl, alignment=None):
    alignment=alignment or {}
    return {
      "ir_version":"1.0",
      "scene_id":scene_dsl["scene_id"],
      "objective":scene_dsl["objective"],
      "duration_mode":"AUDIO_DRIVEN",
      "layers":[
        {"key":f'{scene_dsl["scene_id"]}_layer_{i}',
         "primitive":x["type"],"props":x.get("props",{})}
        for i,x in enumerate(scene_dsl.get("layers",[]))
      ],
      "events":scene_dsl.get("events",[]),
      "camera":scene_dsl.get("camera",[]),
      "assets":scene_dsl.get("assets",[]),
      "sync_anchors":alignment.get("anchors",scene_dsl.get("sync_anchors",[]))
    }
