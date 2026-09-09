def score(model,weights=None):
    w=weights or {"quality":0.5,"cost":0.2,
                  "latency":0.1,"reliability":0.2}
    cost=max(0.0,float(model.get("cost_per_unit",0)))
    latency=max(0.0,float(model.get("latency_ms",0)))
    cost_score=1/(1+cost)
    latency_score=1/(1+latency/1000)
    return (w["quality"]*model.get("quality",0)+
            w["cost"]*cost_score+
            w["latency"]*latency_score+
            w["reliability"]*model.get("reliability",0))

def rank(models,weights=None):
    return sorted(models,key=lambda m:score(m,weights),reverse=True)
