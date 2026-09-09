def plan_layers(elements):
    defaults={"background":0,"diagram":10,"equation":20,"annotation":30,"narration":40}
    planned=[]
    for e in elements:
        layer=e.get("layer",defaults.get(e.get("type"),50))
        planned.append({**e,"z_index":layer})
    return sorted(planned,key=lambda x:(x["z_index"],x["id"]))

def validate_layers(elements):
    ids=[e["id"] for e in elements]
    return {"valid":len(ids)==len(set(ids)),"errors":[] if len(ids)==len(set(ids)) else ["DUPLICATE_LAYER_ID"]}
