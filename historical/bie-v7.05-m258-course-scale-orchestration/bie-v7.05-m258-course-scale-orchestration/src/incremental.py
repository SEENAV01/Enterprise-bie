import hashlib, json

def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

def plan_incremental(previous, current):
    rebuild=[]
    reusable=[]
    for item in current:
        old=previous.get(item["id"])
        new_fp=fingerprint(item.get("inputs",{}))
        if old and old.get("fingerprint")==new_fp:
            reusable.append(item["id"])
        else: rebuild.append(item["id"])
    return {"rebuild":rebuild,"reusable":reusable}
