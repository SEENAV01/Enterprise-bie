def compile_to_remotion_ir(scene_spec):
    # Intermediate representation, intentionally not final React source.
    layers=[]
    for i,l in enumerate(scene_spec.get("layers",[])):
        layers.append({
          "key":f'{scene_spec["scene_id"]}_layer_{i}',
          "primitive":l["type"],
          "props":l["props"]
        })
    return {
      "target":"REMOTION",
      "scene_id":scene_spec["scene_id"],
      "timing_mode":"AUDIO_DRIVEN",
      "layers":layers,
      "events":scene_spec.get("events",[]),
      "camera":scene_spec.get("camera",[]),
      "sync_anchors":scene_spec.get("sync_anchors",[])
    }
