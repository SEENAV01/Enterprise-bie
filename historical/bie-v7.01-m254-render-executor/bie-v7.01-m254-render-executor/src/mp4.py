def validate_mp4_artifact(artifact):
    errors=[]
    if artifact.get("container")!="mp4": errors.append("INVALID_CONTAINER")
    if artifact.get("codec")!="h264": errors.append("INVALID_CODEC")
    if artifact.get("duration_frames",0)<=0: errors.append("INVALID_DURATION")
    return {"valid":not errors,"errors":errors}

def artifact_manifest(result, fps, duration_frames):
    return {"path":result["output"],"container":"mp4","codec":"h264",
            "fps":fps,"duration_frames":duration_frames,"status":"READY"}
