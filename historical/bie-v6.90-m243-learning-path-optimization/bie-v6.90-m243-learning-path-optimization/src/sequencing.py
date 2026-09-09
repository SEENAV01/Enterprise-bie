def score_transition(previous,current,relation_map=None):
    relation_map=relation_map or {}
    prereqs=set(relation_map.get(current,[]))
    return 1.0 if previous in prereqs else 0.5

def optimize_sequence(units,prerequisite_map):
    remaining={u["concept_id"]:u for u in units}; order=[]
    while remaining:
        ready=[cid for cid,u in remaining.items()
               if all(p not in remaining for p in prerequisite_map.get(cid,[]))]
        if not ready: return {"valid":False,"order":order,"remaining":sorted(remaining)}
        ready.sort(key=lambda x:(remaining[x].get("priority",0),x))
        order.extend(ready); [remaining.pop(x) for x in ready]
    return {"valid":True,"order":order,"remaining":[]}
