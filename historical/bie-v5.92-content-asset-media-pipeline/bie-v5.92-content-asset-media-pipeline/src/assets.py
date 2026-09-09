def asset(asset_id,kind,content_hash,mime_type,
          size_bytes=None,metadata=None):
    return {"asset_id":asset_id,"kind":kind,
            "content_hash":content_hash,"mime_type":mime_type,
            "size_bytes":size_bytes,"metadata":metadata or {},
            "schema_version":"5.92"}

def asset_ref(a):
    return {"asset_id":a["asset_id"],
            "content_hash":a["content_hash"],
            "kind":a["kind"]}
