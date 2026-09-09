def slo(name,target,window="rolling"):
    if not 0<target<=1: raise ValueError("INVALID_SLO_TARGET")
    return {"name":name,"target":target,"window":window}
def compliance(observed,target):
    return {"observed":observed,"target":target,
            "compliant":observed>=target}
