def numeric_check(expected,actual,tolerance=0.0):
    if expected is None or actual is None:
        return {"valid":False,"error":"MISSING_VALUE"}
    delta=abs(expected-actual)
    return {"valid":delta<=tolerance,"expected":expected,
            "actual":actual,"delta":delta}

def range_check(value,minimum=None,maximum=None):
    ok=True
    if minimum is not None: ok &= value>=minimum
    if maximum is not None: ok &= value<=maximum
    return {"valid":bool(ok),"value":value,
            "minimum":minimum,"maximum":maximum}
