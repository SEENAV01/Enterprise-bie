def select_path(target,prerequisite_map,mastery,difficulty_history=None):
    difficulty_history=difficulty_history or {}
    order=[]
    seen=set()
    def visit(c):
        if c in seen:return
        seen.add(c)
        for p in prerequisite_map.get(c,[]): visit(p)
        order.append(c)
    visit(target)
    decisions=[]
    for c in order:
        s=mastery.get(c,0)
        decisions.append({"concept_id":c,"mastery":s,
                          "difficulty":choose(c,s,difficulty_history)})
    return {"target":target,"order":order,"decisions":decisions}

def choose(c,score,history):
    if score>=0.85: level="ADVANCED"
    elif score>=0.65: level="INTERMEDIATE"
    else: level="FOUNDATION"
    if history.get(c,{}).get("recent_failures",0)>=2: level="FOUNDATION"
    return level
