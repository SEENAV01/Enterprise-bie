def continuity_contract(global_style_id,asset_ids,motif_ids,motion_language_id):
    return {"global_style_id":global_style_id,"asset_ids":asset_ids,
            "motif_ids":motif_ids,"motion_language_id":motion_language_id}

def check_lesson_continuity(lesson_state,contract):
    errors=[]
    if lesson_state.get("global_style_id")!=contract.get("global_style_id"):
        errors.append("GLOBAL_STYLE_DRIFT")
    unknown=[a for a in lesson_state.get("asset_ids",[])
             if a not in contract.get("asset_ids",[])]
    if unknown: errors.append("UNREGISTERED_ASSET")
    if lesson_state.get("motion_language_id")!=contract.get("motion_language_id"):
        errors.append("MOTION_LANGUAGE_DRIFT")
    return {"valid":not errors,"errors":errors}
