def merge_policy(name="LAST_WRITE_WINS",resolver=None):
    allowed={"LAST_WRITE_WINS","FIRST_WRITE_WINS","CUSTOM","MULTI_VALUE"}
    if name not in allowed:
        raise ValueError("INVALID_MERGE_POLICY")
    return {"name":name,"resolver":resolver}

def resolve(record,policy):
    if policy["name"]=="FIRST_WRITE_WINS":
        return record["left"]
    if policy["name"]=="MULTI_VALUE":
        return [record["left"],record["right"]]
    return record["right"]
