def repair_plan(failures,asset):
    actions=[]
    if "visual" in failures: actions.append("RE_RENDER_VISUAL")
    if "semantic" in failures: actions.append("REGENERATE_SEMANTIC_ELEMENTS")
    if "consistency" in failures: actions.append("MATCH_REFERENCE_LAYOUT")
    if "technical" in failures: actions.append("FIX_TECHNICAL_OUTPUT")
    if not actions: actions.append("ACCEPT")
    return {"asset_id":asset.get("asset_id"),
            "actions":actions,
            "regenerate":any(a.startswith(("RE_RENDER","REGENERATE"))
                              for a in actions)}
