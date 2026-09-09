def update_mastery(prior,evidence_weighted_score,
                   evidence_reliability=1.0):
    p=float(prior.get("estimate",0.0))
    u=float(prior.get("uncertainty",1.0))
    w=max(0.0,min(1.0,evidence_reliability))
    s=max(0.0,min(1.0,evidence_weighted_score))
    new=p+(s-p)*w*0.5
    new_u=max(0.05,u*(1.0-0.35*w))
    out=dict(prior)
    out["estimate"]=new
    out["uncertainty"]=new_u
    return out
