def schema_version(schema_id, version,
                  compatibility="BACKWARD",
                  status="ACTIVE"):
    if compatibility not in {"NONE","BACKWARD","FORWARD","FULL"}:
        raise ValueError("INVALID_COMPATIBILITY")
    return {"schema_id":schema_id,"version":version,
            "compatibility":compatibility,"status":status}

def next_version(current):
    return str(int(current)+1)
