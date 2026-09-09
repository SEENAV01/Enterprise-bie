def asset(asset_id,asset_type,role,description="",accessibility=None):
    return {"asset_id":asset_id,"asset_type":asset_type,"role":role,
            "description":description,"accessibility":accessibility or {}}

def plan_assets(scene_id,requirements):
    return [asset(f"{scene_id}-A{i+1}",r["asset_type"],r["role"],
                  r.get("description",""),r.get("accessibility",{}))
            for i,r in enumerate(requirements)]
