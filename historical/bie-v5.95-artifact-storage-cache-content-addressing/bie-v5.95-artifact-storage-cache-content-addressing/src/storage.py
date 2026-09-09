def storage_location(content_id,backend,
                     uri,tier="STANDARD"):
    return {"content_id":content_id,"backend":backend,
            "uri":uri,"tier":tier}

def storage_record(artifact_ref,locations=None,
                   retention=None):
    return {"artifact":artifact_ref,
            "locations":locations or [],
            "retention":retention or {}}
