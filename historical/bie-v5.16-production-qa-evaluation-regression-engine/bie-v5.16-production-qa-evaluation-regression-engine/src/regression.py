from evaluator import evaluate_scene

def snapshot(scene):
    return {"scene_id":scene.get("scene_id"),
            "duration_in_frames":scene.get("duration_in_frames",0),
            "layer_ids":[x.get("layer_id") for x in scene.get("layers",[])],
            "animation_count":len(scene.get("animations",[]))}

def compare_snapshot(old,new):
    changes=[]
    if old.get("duration_in_frames")!=new.get("duration_in_frames"):
        changes.append("DURATION_CHANGED")
    if old.get("layer_ids")!=new.get("layer_ids"):
        changes.append("LAYERS_CHANGED")
    if old.get("animation_count")!=new.get("animation_count"):
        changes.append("ANIMATIONS_CHANGED")
    return {"changed":bool(changes),"changes":changes}
