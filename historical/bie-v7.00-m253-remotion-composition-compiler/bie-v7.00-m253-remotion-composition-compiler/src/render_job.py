def build_render_job(comp, output="dist/lesson.mp4", codec="h264"):
    return {"composition_id":comp["composition_id"],"output":output,
            "codec":codec,"fps":comp["fps"],"duration_in_frames":comp["duration_in_frames"],
            "status":"READY"}

def validate_render_job(job):
    errors=[]
    if not job.get("composition_id"): errors.append("MISSING_COMPOSITION")
    if not job.get("output"): errors.append("MISSING_OUTPUT")
    if job.get("codec") not in {"h264","vp9","prores"}: errors.append("UNSUPPORTED_CODEC")
    return {"valid":not errors,"errors":errors}
