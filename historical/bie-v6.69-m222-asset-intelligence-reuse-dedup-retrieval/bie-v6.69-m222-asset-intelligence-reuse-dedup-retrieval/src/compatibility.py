def compatible(asset,requirements):
    if requirements.get("asset_type") and asset["asset_type"]!=requirements["asset_type"]:
        return False
    for k,v in requirements.get("metadata",{}).items():
        if asset.get("metadata",{}).get(k)!=v:
            return False
    return True
