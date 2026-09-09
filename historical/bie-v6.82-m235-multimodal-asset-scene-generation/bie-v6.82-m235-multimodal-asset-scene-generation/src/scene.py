def scene(scene_id,title,assets,style,narration,accessibility):
    return {"scene_id":scene_id,"title":title,"assets":assets,
            "style":style,"narration":narration,"accessibility":accessibility}

def validate_scene(s):
    errors=[]
    if not s.get("scene_id"): errors.append("MISSING_SCENE_ID")
    if not s.get("assets"): errors.append("NO_ASSETS")
    if not s.get("narration"): errors.append("NO_NARRATION")
    return {"passed":not errors,"errors":errors}
