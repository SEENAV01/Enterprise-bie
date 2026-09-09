def build_media_graph(scene_id, dependencies):
    nodes=[{"id":scene_id,"kind":"scene"}]
    edges=[]
    for d in dependencies:
        nodes.append({"id":d["id"],"kind":d["kind"]})
        edges.append({"source":d["id"],"target":scene_id,"relation":d.get("relation","REQUIRED")})
    return {"nodes":nodes,"edges":edges}

def validate_media_graph(graph):
    ids={n["id"] for n in graph["nodes"]}
    errors=[e for e in graph["edges"] if e["source"] not in ids or e["target"] not in ids]
    return {"valid":not errors,"errors":errors}
