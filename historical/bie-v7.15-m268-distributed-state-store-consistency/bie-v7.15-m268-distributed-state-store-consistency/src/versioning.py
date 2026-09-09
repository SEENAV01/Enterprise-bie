def make_revision(entity_id, version, payload):
    return {"entity_id":entity_id,"version":version,"payload":payload}

def compare_revision(local, remote):
    if remote["version"]>local["version"]: return "REMOTE_NEWER"
    if remote["version"]<local["version"]: return "LOCAL_NEWER"
    return "EQUAL"
