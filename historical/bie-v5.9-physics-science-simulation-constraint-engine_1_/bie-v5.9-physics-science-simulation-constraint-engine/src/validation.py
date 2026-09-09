def validate_law(law):
    errors=[]
    if not law.get("equation"): errors.append("LAW_MISSING_EQUATION")
    if not law.get("domain"): errors.append("LAW_MISSING_DOMAIN")
    return {"valid":not errors,"errors":errors}

def validate_simulation(sim):
    errors=[]
    if sim.get("dt",0)<=0: errors.append("INVALID_TIME_STEP")
    if sim.get("steps",0)<=0: errors.append("INVALID_STEP_COUNT")
    if not sim.get("equations"): errors.append("NO_SIMULATION_EQUATIONS")
    return {"valid":not errors,"errors":errors}
