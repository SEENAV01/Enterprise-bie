def sync_hook(hook_id,target_id,trigger,offset=0.0):
    return {"hook_id":hook_id,"target_id":target_id,
            "trigger":trigger,"offset":offset}

def sync_plan(items):
    return {"items":items,
            "ordered":sorted(items,key=lambda x:x.get("offset",0.0))}
