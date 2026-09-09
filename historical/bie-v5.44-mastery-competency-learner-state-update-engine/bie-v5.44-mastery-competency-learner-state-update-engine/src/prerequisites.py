def prerequisite_edge(prerequisite_ref,dependent_ref,
                     strength=1.0,reason=None):
    return {"prerequisite_ref":prerequisite_ref,
            "dependent_ref":dependent_ref,
            "strength":strength,"reason":reason}

def readiness_signal(prerequisite_states,required_refs):
    if not required_refs: return 1.0
    values=[]
    for ref in required_refs:
        s=prerequisite_states.get(ref,{})
        values.append(s.get("readiness",0.0))
    return sum(values)/len(values)
