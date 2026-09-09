def sec_to_frame(seconds,fps):
    return round(float(seconds)*fps)

def map_scene(scene,fps):
    return {
      "scene_id":scene["scene_id"],
      "start_frame":sec_to_frame(scene["start_s"],fps),
      "end_frame":sec_to_frame(scene["end_s"],fps),
      "objects":[
        {**o,
         "start_frame":sec_to_frame(o.get("start_s",scene["start_s"]),fps),
         "end_frame":sec_to_frame(o.get("end_s",scene["end_s"]),fps)}
        for o in scene.get("objects",[])
      ]
    }
