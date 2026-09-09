ASSET_TYPES={"image","svg","diagram","table","equation","audio","video","font"}

def resolve_asset(ref, registry):
    if ref not in registry:
        return {"asset_ref":ref,"status":"MISSING","uri":None}
    a=registry[ref]
    return {"asset_ref":ref,"status":"RESOLVED","uri":a.get("uri"),"type":a.get("type")}

def resolve_scene_assets(scene, registry):
    return [resolve_asset(x,registry) for x in scene.get("visual",{}).get("assets",[])]
