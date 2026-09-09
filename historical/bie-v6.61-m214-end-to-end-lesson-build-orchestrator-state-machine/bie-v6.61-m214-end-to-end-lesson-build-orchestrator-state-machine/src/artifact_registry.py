def artifact(artifact_id, artifact_type, uri,
             stage, checksum=None, metadata=None):
    return {"artifact_id":artifact_id,"artifact_type":artifact_type,
            "uri":uri,"stage":stage,"checksum":checksum,
            "metadata":metadata or {}}

def registry(artifacts):
    return {"artifacts":artifacts}

def valid(a):
    return bool(a["artifact_id"] and a["artifact_type"] and a["uri"] and a["stage"])
