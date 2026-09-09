def asset(asset_id,asset_type,uri,metadata=None,tags=None,
          checksum=None,version=1):
    return {"asset_id":asset_id,"asset_type":asset_type,"uri":uri,
            "metadata":metadata or {},"tags":tags or [],
            "checksum":checksum,"version":version}

def valid(a):
    return bool(a["asset_id"] and a["asset_type"] and a["uri"])
