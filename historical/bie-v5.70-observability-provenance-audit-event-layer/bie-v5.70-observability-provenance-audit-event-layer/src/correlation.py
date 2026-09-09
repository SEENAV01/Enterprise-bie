def correlation_id(root_id,stage=None):
    return root_id if stage is None else f"{root_id}:{stage}"

def trace(events,root_id):
    return [e for e in events if e.get("correlation_id","").startswith(root_id)]
