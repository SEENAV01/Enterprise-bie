def artifact(artifact_id,content_id,size_bytes,
             media_type,metadata=None):
    return {"artifact_id":artifact_id,
            "content_id":content_id,"size_bytes":size_bytes,
            "media_type":media_type,
            "metadata":metadata or {},
            "immutable":True,"schema_version":"5.95"}

def artifact_ref(a):
    return {"artifact_id":a["artifact_id"],
            "content_id":a["content_id"]}
