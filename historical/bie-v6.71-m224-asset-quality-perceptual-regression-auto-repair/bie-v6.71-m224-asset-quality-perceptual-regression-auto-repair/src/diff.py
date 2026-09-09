def visual_diff(reference,current):
    ref=set(reference.get("features",[]))
    cur=set(current.get("features",[]))
    return {"added":sorted(cur-ref),"removed":sorted(ref-cur),
            "unchanged":sorted(ref&cur)}
