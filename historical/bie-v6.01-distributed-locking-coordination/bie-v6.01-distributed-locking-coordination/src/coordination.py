def coordination_state(key,value,
                       version=1,owner=None):
    return {"key":key,"value":value,
            "version":version,"owner":owner}

def compare_and_set(current,expected_version,
                    value,owner=None):
    if current.get("version")!=expected_version:
        raise ValueError("COORDINATION_VERSION_CONFLICT")
    return {"key":current["key"],"value":value,
            "version":expected_version+1,
            "owner":owner}
