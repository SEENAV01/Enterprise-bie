from checks import check_structure,check_timing,check_sync

def evaluate_scene(scene):
    errors=[]
    errors+=check_structure(scene)
    errors+=check_timing(scene)
    errors+=check_sync(scene)
    return {"scene_id":scene.get("scene_id"),"passed":not errors,"errors":errors}

def evaluate_course(scenes):
    results=[evaluate_scene(s) for s in scenes]
    errors=[e for r in results for e in r["errors"]]
    return {"passed":not errors,"scene_results":results,"errors":errors}
