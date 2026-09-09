def validate_scene(scene):
    errors=[]; warnings=[]
    if scene["end_s"]<=scene["start_s"]:
        errors.append("INVALID_SCENE_DURATION")
    ids=set()
    for o in scene.get("objects",[]):
        if o["id"] in ids: errors.append("DUPLICATE_OBJECT_ID")
        ids.add(o["id"])
        if o["kind"]=="TEXT" and len(o.get("content",""))>120:
            warnings.append("TEXT_TOO_LONG")
    for l in scene.get("lifecycles",[]):
        if l["object_id"] not in ids: errors.append("UNKNOWN_OBJECT")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
