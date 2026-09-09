def build_metadata(comp, scene):
    return {"composition_id":comp["composition_id"],"title":scene.get("title","Educational Scene"),
            "fps":comp["fps"],"duration_in_frames":comp["duration_in_frames"],
            "dimensions":[comp["width"],comp["height"]],"renderer":"Remotion"}

def validate_metadata(meta):
    return {"valid":bool(meta.get("composition_id") and meta.get("renderer")),
            "errors":[] if meta.get("composition_id") and meta.get("renderer") else ["INVALID_METADATA"]}
