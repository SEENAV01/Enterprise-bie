def create_render_request(job, project_dir):
    return {"composition_id":job["composition_id"],"project_dir":project_dir,
            "output":job["output"],"codec":job["codec"],
            "fps":job["fps"],"duration_in_frames":job["duration_in_frames"],
            "status":"QUEUED"}

def execute_render(request, executor="remotion-cli"):
    # Adapter boundary: production implementation invokes the configured renderer.
    return {**request,"executor":executor,"status":"RENDERED",
            "output":request["output"]}

def validate_render_result(result):
    errors=[]
    if result.get("status")!="RENDERED": errors.append("RENDER_NOT_COMPLETE")
    if not result.get("output"): errors.append("OUTPUT_MISSING")
    return {"valid":not errors,"errors":errors}
