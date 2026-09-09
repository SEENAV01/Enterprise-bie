def cognitive_load(unit):
    intrinsic=float(unit.get("intrinsic_load",0.5))
    extraneous=float(unit.get("extraneous_load",0.2))
    germane=float(unit.get("germane_load",0.3))
    return {"intrinsic":intrinsic,"extraneous":extraneous,"germane":germane,
            "total":round(intrinsic+extraneous+germane,3)}

def validate_load(load,max_total=1.5,max_extraneous=0.4):
    errors=[]
    if load["total"]>max_total: errors.append("TOTAL_LOAD_HIGH")
    if load["extraneous"]>max_extraneous: errors.append("EXTRANEOUS_LOAD_HIGH")
    return {"passed":not errors,"errors":errors}
