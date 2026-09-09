def merge_nodes(source_nodes, expansion_nodes):
    merged={}
    for n in source_nodes+expansion_nodes:
        key=n.get("concept_id") or n.get("id")
        if key not in merged:
            merged[key]={**n,"origins":[]}
        merged[key]["origins"].append(
            "SOURCE" if n in source_nodes else "EXPANSION"
        )
    return list(merged.values())
