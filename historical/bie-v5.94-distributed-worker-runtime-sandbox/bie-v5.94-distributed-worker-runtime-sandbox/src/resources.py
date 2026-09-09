def resources(cpu=0,memory_mb=0,gpu=0,disk_mb=0):
    return {"cpu":cpu,"memory_mb":memory_mb,
            "gpu":gpu,"disk_mb":disk_mb}

def within_limits(required,available):
    return all(available.get(k,0)>=v
               for k,v in required.items())
