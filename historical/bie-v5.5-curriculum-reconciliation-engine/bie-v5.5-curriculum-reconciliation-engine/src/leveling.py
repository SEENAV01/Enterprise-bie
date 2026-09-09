LEVELS={"FOUNDATION":0,"INTERMEDIATE":1,"ADVANCED":2,"EXPERT":3}

def level_fit(node,learner_level):
    level=node.get("level","FOUNDATION")
    return LEVELS.get(level,0)<=LEVELS.get(learner_level,0)

def adapt_depth(nodes,learner_level):
    result=[]
    for n in nodes:
        x=dict(n)
        x["delivery"]="CORE" if level_fit(n,learner_level) else "DEEP_DIVE"
        result.append(x)
    return result
