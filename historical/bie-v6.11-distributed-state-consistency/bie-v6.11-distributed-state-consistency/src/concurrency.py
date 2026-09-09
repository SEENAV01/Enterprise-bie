def update_if_version(record,
                     expected_version,
                     new_state):
    if record.get("version") != expected_version:
        return {"status":"CONFLICT",
                "current_version":record.get("version")}
    out=dict(record)
    out["state"]=new_state
    out["version"]=expected_version+1
    return {"status":"UPDATED","entity":out}
