def scene_spec(scene_id,semantic_refs=None,
               visual_elements=None,actions=None,
               narration=None,timing=None,parameters=None):
    return {"scene_id":scene_id,"semantic_refs":semantic_refs or [],
            "visual_elements":visual_elements or [],
            "actions":actions or [],"narration":narration,
            "timing":timing or {},"parameters":parameters or {}}

def scene_dependency_refs(scene):
    return sorted(set(scene.get("semantic_refs",[])))
