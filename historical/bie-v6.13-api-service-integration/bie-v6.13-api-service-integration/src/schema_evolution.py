def schema_version(name,version,
                   compatibility="BACKWARD",
                   deprecated=False):
    return {"name":name,"version":version,
            "compatibility":compatibility,
            "deprecated":deprecated}

def compatible(old,new):
    return old.get("compatibility") == new.get("compatibility")
