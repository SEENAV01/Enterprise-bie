def regression(baseline,current,
               absolute_tolerance=0.0,
               relative_tolerance=0.0):
    delta=current-baseline
    relative=(delta/baseline) if baseline else 0.0
    failed=(delta < -absolute_tolerance and
            relative < -relative_tolerance)
    return {"baseline":baseline,"current":current,
            "delta":delta,"relative_delta":relative,
            "regression":failed}

def compare_cases(baseline,current):
    out={}
    for case_id,base in baseline.items():
        if case_id in current:
            out[case_id]=regression(base,current[case_id])
    return out
