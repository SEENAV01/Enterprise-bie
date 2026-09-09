def capacity_unit(name, scale=1):
    if scale <= 0:
        raise ValueError("INVALID_UNIT_SCALE")
    return {"name":name,"scale":scale}

def normalize(value, record):
    return value * record["scale"]
