def asset(asset_id,asset_type,version,content_hash,
          status="ACTIVE",metadata=None,tags=None):
    return {"asset_id":asset_id,"asset_type":asset_type,
            "version":version,"content_hash":content_hash,
            "status":status,"metadata":metadata or {},
            "tags":tags or []}

def register_asset(registry,item):
    registry[item["asset_id"]+"@"+item["version"]]=item
    return registry
