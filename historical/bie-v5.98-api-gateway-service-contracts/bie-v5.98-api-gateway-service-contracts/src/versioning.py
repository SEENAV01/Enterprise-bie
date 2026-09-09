def api_version(version,phase="CURRENT",
               deprecated=False):
    return {"version":version,"phase":phase,
            "deprecated":deprecated}

def compatibility(old_schema,new_schema):
    return old_schema==new_schema or (
        isinstance(old_schema,dict) and
        isinstance(new_schema,dict) and
        set(old_schema).issubset(new_schema)
    )
