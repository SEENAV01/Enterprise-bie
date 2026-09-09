def validate_plan(sequence,target_concepts,prerequisite_map):
    pos={c:i for i,c in enumerate(sequence)}
    errors=[]
    for t in target_concepts:
        for p in prerequisite_map.get(t,[]):
            if p not in pos: errors.append({"target":t,"missing":p})
            elif pos[p]>=pos[t]: errors.append({"target":t,"prerequisite":p,"error":"WRONG_ORDER"})
    return {"passed":not errors,"errors":errors}
