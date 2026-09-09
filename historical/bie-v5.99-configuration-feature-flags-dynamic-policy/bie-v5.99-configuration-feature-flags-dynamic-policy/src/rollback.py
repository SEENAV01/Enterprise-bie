def revision(key,version,value,created_at):
    return {"key":key,"version":version,
            "value":value,"created_at":created_at}

def latest_before(revisions,version):
    valid=[r for r in revisions if r["version"]<=version]
    return max(valid,key=lambda r:r["version"]) if valid else None
