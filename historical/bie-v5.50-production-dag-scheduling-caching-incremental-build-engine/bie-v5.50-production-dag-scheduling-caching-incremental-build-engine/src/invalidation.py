def invalidate_nodes(changed_ids,nodes):
    changed=set(changed_ids)
    invalid=set(changed)
    progress=True
    while progress:
        progress=False
        for n in nodes:
            if n["node_id"] in invalid: continue
            if any(d in invalid for d in n.get("dependencies",[])):
                invalid.add(n["node_id"]); progress=True
    return sorted(invalid)
