def qa_scene(scene, audio=None, rendered=None):
    errors=[]; warnings=[]
    if not scene.get("scene_id"): errors.append("NO_SCENE_ID")
    if scene.get("duration",{}).get("mode")!="AUDIO_DRIVEN":
        errors.append("NON_AUDIO_TIMING")
    if not scene.get("narration_unit_ids"):
        errors.append("NO_NARRATION_LINK")
    if not scene.get("layers") and scene.get("scene_type") not in ["PAUSE","TRANSITION"]:
        warnings.append("NO_VISUAL_LAYERS")
    if rendered:
        if rendered.get("render_failed"): errors.append("RENDER_FAILED")
        if rendered.get("audio_missing"): errors.append("AUDIO_MISSING")
        if rendered.get("overflow_detected"): errors.append("TEXT_OVERFLOW")
    return {"status":"FAIL" if errors else "PASS","errors":errors,"warnings":warnings}

def course_qa(scene_reports):
    failures=[x for x in scene_reports if x["status"]=="FAIL"]
    return {
      "status":"FAIL" if failures else "PASS",
      "failed_scene_ids":[x.get("scene_id") for x in failures],
      "total_scenes":len(scene_reports)
    }
