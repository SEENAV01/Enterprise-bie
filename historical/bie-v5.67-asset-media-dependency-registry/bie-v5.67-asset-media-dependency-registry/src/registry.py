from assets import asset_key

def registry(records=None,relations=None):
    return {"assets":records or [],"relations":relations or []}

def register(reg,record):
    out=dict(reg)
    out["assets"]=list(reg.get("assets",[]))
    key=asset_key(record)
    if any(asset_key(x)==key for x in out["assets"]):
        raise ValueError("ASSET_VERSION_ALREADY_REGISTERED")
    out["assets"].append(record)
    return out

def find(reg,asset_id,version=None):
    for x in reg.get("assets",[]):
        if x.get("asset_id")==asset_id and (
            version is None or x.get("version")==version):
            return x
    return None
