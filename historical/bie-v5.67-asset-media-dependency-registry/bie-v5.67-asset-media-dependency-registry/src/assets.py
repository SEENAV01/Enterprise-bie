def asset(asset_id,version,asset_type,uri=None,
          content_hash=None,mime_type=None,metadata=None):
    return {"asset_id":asset_id,"version":version,
            "asset_type":asset_type,"uri":uri,
            "content_hash":content_hash,"mime_type":mime_type,
            "metadata":metadata or {}}

def asset_key(asset_record):
    return f"{asset_record['asset_id']}@{asset_record['version']}"
