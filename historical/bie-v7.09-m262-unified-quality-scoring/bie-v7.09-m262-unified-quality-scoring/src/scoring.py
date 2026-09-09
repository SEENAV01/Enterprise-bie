def weighted_score(checks, weights):
    total=0.0; weight_total=0.0
    for name,result in checks.items():
        w=weights.get(name,1.0)
        total += (100.0 if result.get("valid") else 0.0)*w
        weight_total += w
    return round(total/max(weight_total,1e-9),2)

def score_domains(checks, weights):
    return {name:(100.0 if r.get("valid") else 0.0) for name,r in checks.items()} | {
        "overall":weighted_score(checks,weights)}
