def focus_plan(objects, active_ids):
    result=[]
    active=set(active_ids)
    for o in objects:
        oid=o["id"]
        if oid in active:
            result.append({"object_id":oid,"opacity":1.0,"emphasis":True})
        elif o.get("role")=="DECORATIVE":
            result.append({"object_id":oid,"opacity":0.25,"emphasis":False})
        else:
            result.append({"object_id":oid,"opacity":0.65,"emphasis":False})
    return result
