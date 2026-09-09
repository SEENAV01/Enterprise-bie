def check_terminology(unit_text, global_memory):
    issues=[]
    for term,entry in global_memory.get("terminology",{}).items():
        canonical=entry.get("canonical",term)
        alternatives=entry.get("avoid",[])
        for a in alternatives:
            if a in unit_text and canonical not in unit_text:
                issues.append({"type":"NON_CANONICAL_TERM","found":a,"expected":canonical})
    return issues

def check_style(scene, global_memory):
    profile=global_memory.get("style_profile",{})
    return {
      "scene_id":scene.get("scene_id"),
      "style_version":profile.get("version","1"),
      "required":profile.get("required",[])
    }
