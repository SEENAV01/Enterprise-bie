def prerequisite_order(objective_ids, relations):
    incoming={x:0 for x in objective_ids}; children={x:[] for x in objective_ids}
    for a,b in relations:
        if a in children and b in incoming:
            children[a].append(b); incoming[b]+=1
    q=[x for x,v in incoming.items() if v==0]; order=[]
    while q:
        x=q.pop(0); order.append(x)
        for y in children[x]:
            incoming[y]-=1
            if incoming[y]==0:q.append(y)
    return order, len(order)!=len(objective_ids)

def compile_pedagogy(objectives, relations, strategies=None, examples=None,
                      misconceptions=None, practice=None, checkpoints=None):
    ids=[x["objective_id"] for x in objectives]
    order,cycle=prerequisite_order(ids,relations)
    return {
      "schema_version":"5.33",
      "objective_order":order,
      "learning_sequence":{
        "objectives":objectives,"strategies":strategies or [],
        "examples":examples or [],"practice":practice or [],
        "checkpoints":checkpoints or []
      },
      "misconceptions":misconceptions or [],
      "quality_gate":{"valid":not cycle,
                      "errors":["OBJECTIVE_DEPENDENCY_CYCLE"] if cycle else []}
    }
