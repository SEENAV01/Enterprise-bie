def consistency_check(records):
    errors=[]
    for key,versions in records.items():
        expected=1
        for version in sorted(versions):
            if version!=expected:
                errors.append(f"VERSION_GAP:{key}:{expected}->{version}")
            expected=version+1
    return {"consistent":not errors,"errors":errors}

def merge_state(local, remote):
    merged=dict(local)
    conflicts=[]
    for key,item in remote.items():
        if key not in merged or item["version"]>merged[key]["version"]:
            merged[key]=item
        elif item["version"]==merged[key]["version"] and item["value"]!=merged[key]["value"]:
            conflicts.append(key)
    return {"state":merged,"conflicts":conflicts}
