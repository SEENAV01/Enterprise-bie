def artifact_output(artifact_id,path,content_hash,
                    mime_type,size_bytes):
    return {"artifact_id":artifact_id,"path":path,
            "content_hash":content_hash,
            "mime_type":mime_type,"size_bytes":size_bytes}

def output_allowed(artifact,limits):
    return artifact.get("size_bytes",0) <= limits.get("max_output_mb",0)*1024*1024
