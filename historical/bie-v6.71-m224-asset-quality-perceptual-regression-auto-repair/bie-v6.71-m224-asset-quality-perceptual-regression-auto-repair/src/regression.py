def regression_check(baseline,current,tolerance=0.05):
    keys=set(baseline)|set(current)
    diffs={}
    for k in keys:
        b=float(baseline.get(k,0)); c=float(current.get(k,0))
        diffs[k]=abs(c-b)
    failures={k:v for k,v in diffs.items() if v>tolerance}
    return {"passed":not failures,"differences":diffs,
            "failures":failures,"tolerance":tolerance}
