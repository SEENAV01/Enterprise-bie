def procedural_spec(generator,seed,parameters):
    return {"generator":generator,"seed":seed,"parameters":parameters}

def deterministic(spec):
    return bool(spec["generator"] and spec["seed"] is not None)
