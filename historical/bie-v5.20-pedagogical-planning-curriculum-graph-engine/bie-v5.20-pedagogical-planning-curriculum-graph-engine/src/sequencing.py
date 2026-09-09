def sequence_events(events):
    return sorted(events,key=lambda x:x.get("order",0))

def check_prerequisites(event_concepts,ordered_concepts,edges):
    position={c:i for i,c in enumerate(ordered_concepts)}
    violations=[]
    for e in edges:
        a,b=e["from_concept"],e["to_concept"]
        if a in position and b in position and position[a]>position[b]:
            violations.append({"from_concept":a,"to_concept":b})
    return {"valid":not violations,"violations":violations}
