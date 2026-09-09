def next_version(asset):
    return asset.get("version",0)+1

def version_ref(asset):
    return f'{asset["asset_id"]}@v{asset.get("version",1)}'
