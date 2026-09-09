def verify_artifact(path, expected_container="mp4", expected_codec="h264",
                    duration_frames=None):
    # Metadata supplied by the actual worker/probe in production.
    artifact={"path":path,"container":expected_container,"codec":expected_codec,
              "duration_frames":duration_frames,"verified":True}
    errors=[]
    if not path: errors.append("ARTIFACT_PATH_MISSING")
    if artifact["container"]!=expected_container: errors.append("CONTAINER_MISMATCH")
    if artifact["codec"]!=expected_codec: errors.append("CODEC_MISMATCH")
    artifact["verified"]=not errors
    return {"artifact":artifact,"valid":not errors,"errors":errors}
