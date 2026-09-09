def adapt_unit(unit, learner):
    level=learner.get("level","intermediate")
    prior=learner.get("mastery",{}).get(unit["knowledge_id"],0)
    u=dict(unit)
    if level=="beginner" or prior<0.4:
        u["depth"]="FOUNDATIONAL"
        u["extra_intuition"]=True
        u["extra_example"]=True
    elif prior>=0.8:
        u["depth"]="COMPACT"
        u["extra_intuition"]=False
    else:
        u["depth"]="STANDARD"
        u["extra_intuition"]=True
    return u
