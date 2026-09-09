def consistency_check(scene, style, assets):
    errors=[]; warnings=[]
    if scene.get("style_id")!=style.get("style_id"):
        errors.append("STYLE_BIBLE_MISMATCH")
    known={a["asset_id"] for a in assets}
    for ref in scene.get("asset_refs",[]):
        if ref.get("asset_id") not in known:
            errors.append("UNKNOWN_ASSET")
    if not scene.get("visual_grammar_id"):
        warnings.append("MISSING_VISUAL_GRAMMAR")
    return {"valid":not errors,"errors":errors,"warnings":warnings}
