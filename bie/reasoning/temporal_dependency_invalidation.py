"""RE-TEMP-042 — Propagate temporal-result invalidation through derived dependencies."""
def invalidate_temporal_dependents(changed_ids, dependency_edges):
    changed=set(changed_ids); reverse={}
    for parent,child in dependency_edges: reverse.setdefault(parent,set()).add(child)
    queue=sorted(changed); impacted=set()
    while queue:
        n=queue.pop(0)
        for child in sorted(reverse.get(n,())):
            if child not in impacted and child not in changed:
                impacted.add(child); queue.append(child)
    return tuple(sorted(impacted))
