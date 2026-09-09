def invalidation_event(event_id,changed_refs,reason,
                      source="SYSTEM"):
    return {"event_id":event_id,"changed_refs":changed_refs,
            "reason":reason,"source":source}

def invalidate_dependents(graph,changed_refs):
    invalidated=set(changed_refs)
    changed=True
    while changed:
        changed=False
        for e in graph.get("edges",[]):
            if e["source"] in invalidated and e["target"] not in invalidated:
                invalidated.add(e["target"])
                changed=True
    return sorted(invalidated)
