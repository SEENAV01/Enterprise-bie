def validate_ir(ir):
    errors=[]
    ids=[x["layer_id"] for x in ir.get("layers",[])]
    if len(ids)!=len(set(ids)): errors.append("DUPLICATE_LAYER_ID")
    if ir["canvas"]["fps"]<=0: errors.append("INVALID_FPS")
    if ir.get("duration_in_frames",0)<0: errors.append("INVALID_DURATION")
    for a in ir.get("animations",[]):
        if a["target_id"] not in ids: errors.append("ANIMATION_TARGET_MISSING")
    return {"valid":not errors,"errors":errors}
