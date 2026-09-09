def asset_version(asset_id,version,parent=None,
                  content_hash=None,change_summary=None):
    return {"asset_id":asset_id,"version":version,"parent":parent,
            "content_hash":content_hash,
            "change_summary":change_summary}

def latest_version(registry,asset_id):
    matches=[v for k,v in registry.items()
             if v.get("asset_id")==asset_id]
    return max(matches,key=lambda x:x.get("version",""))
