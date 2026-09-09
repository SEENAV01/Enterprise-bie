def lock_entry(name,version,source=None,
               integrity=None):
    return {"name":name,"version":version,
            "source":source,"integrity":integrity}

def dependency_lock(entries=None):
    return {"lock_version":"1","entries":entries or []}
