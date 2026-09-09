def permission(action, resource, conditions=None):
    return {"action":action,"resource":resource,
            "conditions":conditions or {}}

def matches(record, action, resource):
    return record["action"]==action and record["resource"]==resource
