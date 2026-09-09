def dependency_graph(scenes, assets):
    nodes=[]; edges=[]
    for s in scenes:
        sid=s["scene_id"]; nodes.append({"id":sid,"type":"scene"})
        for a in s.get("asset_refs",[]):
            aid=a["asset_id"]; nodes.append({"id":aid,"type":"asset"})
            edges.append({"from":sid,"to":aid,"relation":"REQUIRES"})
    unique={n["id"]:n for n in nodes}
    return {"nodes":list(unique.values()),"edges":edges}
