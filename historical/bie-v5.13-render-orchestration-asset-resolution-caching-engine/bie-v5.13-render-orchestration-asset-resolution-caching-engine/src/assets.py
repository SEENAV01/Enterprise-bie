def resolve_assets(asset_refs, asset_library):
    by_id={a["asset_id"]:a for a in asset_library}
    resolved=[]; missing=[]
    for ref in asset_refs:
        aid=ref["asset_id"]
        if aid in by_id:
            resolved.append({"asset_id":aid,"asset":by_id[aid],"status":"RESOLVED"})
        else:
            missing.append(aid)
    return {"resolved":resolved,"missing":missing}
