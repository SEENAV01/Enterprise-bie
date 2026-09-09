def scope(resource_pattern, constraints=None):
    return {"resource_pattern":resource_pattern,
            "constraints":constraints or {}}

def matches(record, resource):
    pattern=record["resource_pattern"]
    return pattern=="*" or pattern==resource
