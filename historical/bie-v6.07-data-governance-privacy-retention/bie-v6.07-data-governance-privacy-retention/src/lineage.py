def lineage(resource_id,parents=None,
            transformations=None):
    return {"resource_id":resource_id,
            "parents":parents or [],
            "transformations":transformations or []}

def add_parent(record,parent_id):
    out=dict(record)
    out["parents"]=list(out.get("parents",[]))+[parent_id]
    return out
