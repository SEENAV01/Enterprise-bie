def sync_rule(narration_id,visual_id,relation,offset="ON_CUE"):
    return {"narration_id":narration_id,"visual_id":visual_id,
            "relation":relation,"offset":offset}

def synchronize(narration_events,visual_events):
    links=[]
    for n,v in zip(narration_events,visual_events):
        links.append(sync_rule(n["id"],v["id"],"VISUAL_SUPPORTS_NARRATION"))
    return links
