def validate_dimensions(asset,expected):
    return asset.get("width")==expected.get("width") and            asset.get("height")==expected.get("height")

def validate_metadata(asset,requirements):
    return all(asset.get("metadata",{}).get(k)==v
               for k,v in requirements.items())

def validate_asset(asset,requirements):
    checks={
      "dimensions":validate_dimensions(asset,requirements.get("dimensions",{}))
        if requirements.get("dimensions") else True,
      "metadata":validate_metadata(asset,requirements.get("metadata",{})),
      "uri":bool(asset.get("uri")),
      "type":asset.get("asset_type")==requirements.get("asset_type")
        if requirements.get("asset_type") else True
    }
    return {"checks":checks,"passed":all(checks.values())}
