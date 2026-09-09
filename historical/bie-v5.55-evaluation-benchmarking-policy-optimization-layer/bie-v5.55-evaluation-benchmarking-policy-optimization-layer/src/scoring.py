def objective(name,value,direction="maximize",
             weight=1.0,target=None,tolerance=None):
    return {"name":name,"value":value,"direction":direction,
            "weight":weight,"target":target,"tolerance":tolerance}

def normalize(value,low,high,direction="maximize"):
    if high==low: return 1.0
    x=max(0,min(1,(value-low)/(high-low)))
    return x if direction=="maximize" else 1-x

def multi_objective_score(objectives):
    total=0.0
    weight_sum=0.0
    for o in objectives:
        if "normalized" not in o: continue
        w=o.get("weight",1.0)
        total += o["normalized"]*w
        weight_sum += w
    return total/weight_sum if weight_sum else None
