def batch_plan(chunks:list[dict],batch_size:int=8)->list[list[dict]]:
    return [chunks[i:i+batch_size] for i in range(0,len(chunks),batch_size)]

def reduce_units(units:list[dict])->dict:
    # Keep provenance while merging; no claim is allowed to lose its evidence.
    merged={}
    for u in units:
        key=u["unit_id"]
        if key not in merged:
            merged[key]=u
        else:
            merged[key]["source_refs"]=list(dict.fromkeys(
                merged[key].get("source_refs",[])+u.get("source_refs",[])
            ))
            merged[key]["claims"]+=u.get("claims",[])
            merged[key]["uncertainties"]+=u.get("uncertainties",[])
    return {"units":list(merged.values())}
