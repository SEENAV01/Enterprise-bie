def routing_policy(policy_id,algorithm="WEIGHTED",
                   health_required=True):
    return {"policy_id":policy_id,
            "algorithm":algorithm,
            "health_required":health_required}

def eligible(instances,health=None):
    health=health or {}
    return [x for x in instances
            if (not health or health.get(x["instance_id"])== "HEALTHY")
            and x.get("status") in {"REGISTERED","HEALTHY","READY"}]

def weighted_choice(instances,subject_hash):
    if not instances: return None
    total=sum(max(0,x.get("weight",1)) for x in instances)
    if total<=0: return instances[0]
    point=subject_hash%total
    for item in instances:
        point-=max(0,item.get("weight",1))
        if point<0: return item
    return instances[-1]
