def recover(instance, event_log):
    state=instance["state"]
    for e in event_log:
        state=e.get("to",state)
    instance["state"]=state
    return instance

def is_resumable(instance):
    return instance["status"]=="RUNNING" and bool(instance["workflow_id"])
