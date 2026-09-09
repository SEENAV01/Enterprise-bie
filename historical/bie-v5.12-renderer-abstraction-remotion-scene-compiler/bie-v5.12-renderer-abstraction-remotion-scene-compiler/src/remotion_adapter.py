def remotion_composition(scene_ir):
    return {"renderer":"remotion",
      "composition":{"id":scene_ir["scene_id"],
        "width":scene_ir["canvas"]["width"],"height":scene_ir["canvas"]["height"],
        "fps":scene_ir["canvas"]["fps"],
        "durationInFrames":scene_ir.get("duration_in_frames",0)},
      "layers":scene_ir["layers"],"animations":scene_ir["animations"],
      "audio":scene_ir["audio"],"captions":scene_ir["captions"],
      "transitions":scene_ir["transitions"]}
