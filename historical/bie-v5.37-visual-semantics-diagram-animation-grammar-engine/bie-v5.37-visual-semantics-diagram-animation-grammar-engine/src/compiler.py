def compile_visual_scene(scene,animations=None,layout=None):
    ids={p["primitive_id"] for p in scene.get("primitives",[])}
    errors=[]
    for r in scene.get("relations",[]):
        if r.get("source") not in ids or r.get("target") not in ids:
            errors.append("VISUAL_RELATION_TARGET_MISSING")
    for a in animations or []:
        if a.get("target") not in ids:
            errors.append("ANIMATION_TARGET_MISSING")
    return {"schema_version":"5.37",
            "scene":scene,"animations":animations or [],
            "layout":layout or {},
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
