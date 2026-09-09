def compile_composition(scene):
    return {
        "composition_id": scene["scene_id"],
        "width": scene.get("width",1920),
        "height": scene.get("height",1080),
        "fps": scene["fps"],
        "duration_in_frames": scene["duration_in_frames"],
        "component_name": "GeneratedEducationalScene"
    }

def validate_composition(comp):
    required=["composition_id","width","height","fps","duration_in_frames","component_name"]
    errors=[x for x in required if x not in comp]
    if comp.get("fps",0)<=0: errors.append("INVALID_FPS")
    if comp.get("duration_in_frames",0)<=0: errors.append("INVALID_DURATION")
    return {"valid":not errors,"errors":errors}
