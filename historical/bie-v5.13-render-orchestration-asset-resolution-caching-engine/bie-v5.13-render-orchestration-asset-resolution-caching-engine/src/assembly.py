def assembly_manifest(rendered_scenes, fps, width, height):
    ordered=sorted(rendered_scenes,key=lambda x:x.get("sequence_index",0))
    return {"fps":fps,"width":width,"height":height,
            "scenes":ordered,
            "final_status":"READY_FOR_ASSEMBLY"}

def validate_assembly(manifest):
    errors=[]
    ids=[s["scene_id"] for s in manifest.get("scenes",[])]
    if len(ids)!=len(set(ids)): errors.append("DUPLICATE_SCENE")
    if manifest.get("fps",0)<=0: errors.append("INVALID_FPS")
    return {"valid":not errors,"errors":errors}
