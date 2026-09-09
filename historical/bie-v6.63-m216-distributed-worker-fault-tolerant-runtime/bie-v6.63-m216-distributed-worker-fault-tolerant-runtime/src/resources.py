def resource_pool(cpu=8,memory=32,gpu=0):
    if min(cpu,memory,gpu)<0:
        raise ValueError("INVALID_RESOURCE_CAPACITY")
    return {"cpu":cpu,"memory":memory,"gpu":gpu}

def fits(request,available):
    return all(request.get(k,0)<=available.get(k,0)
               for k in ("cpu","memory","gpu"))

def allocate(request,available):
    if not fits(request,available):
        raise ValueError("INSUFFICIENT_RESOURCES")
    return {k:available.get(k,0)-request.get(k,0)
            for k in ("cpu","memory","gpu")}
