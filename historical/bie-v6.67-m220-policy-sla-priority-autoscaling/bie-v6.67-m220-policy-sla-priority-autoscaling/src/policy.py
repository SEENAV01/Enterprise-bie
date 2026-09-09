def policy(name,priority_class,deadline_seconds=None,
           preemptible=False,max_retries=3):
    return {"name":name,"priority_class":priority_class,
            "deadline_seconds":deadline_seconds,
            "preemptible":preemptible,"max_retries":max_retries}

def validate(p):
    return bool(p["name"] and p["priority_class"]) and p["max_retries"]>=0
