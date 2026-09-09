def update_request(key,new_value,
                  expected_version=None,actor=None,
                  reason=None):
    return {"key":key,"new_value":new_value,
            "expected_version":expected_version,
            "actor":actor,"reason":reason}

def apply_update(current,request):
    expected=request.get("expected_version")
    if expected is not None and current.get("version")!=expected:
        raise ValueError("CONFIG_VERSION_CONFLICT")
    out=dict(current)
    out["value"]=request["new_value"]
    out["version"]=current.get("version",0)+1
    return out
