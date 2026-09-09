def reuse_plan(request, candidates):
    if not candidates:
        return {"action":"GENERATE_NEW","asset_id":None}
    best=candidates[0]
    if best.get("score",0)>0:
        return {"action":"REUSE","asset_id":best["asset_id"]}
    return {"action":"GENERATE_NEW","asset_id":None}
