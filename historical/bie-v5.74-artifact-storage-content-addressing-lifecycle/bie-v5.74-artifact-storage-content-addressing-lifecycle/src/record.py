def artifact_record(artifact_id,artifact_type,size_bytes,
                    content_hash_value,media_type=None,
                    metadata=None,parents=None):
    return {"artifact_id":artifact_id,"artifact_type":artifact_type,
            "size_bytes":size_bytes,
            "content_hash":content_hash_value,
            "media_type":media_type,
            "metadata":metadata or {},
            "parents":parents or []}
