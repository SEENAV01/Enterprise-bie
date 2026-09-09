def lineage_edge(source_id, target_id,
                 transformation=None, relation="DERIVES_FROM"):
    if relation not in {"DERIVES_FROM","COPIED_FROM","AGGREGATED_FROM","SPLIT_FROM"}:
        raise ValueError("INVALID_LINEAGE_RELATION")
    return {"source_id":source_id,"target_id":target_id,
            "transformation":transformation,"relation":relation}

def connects(edge,source_id,target_id):
    return edge["source_id"]==source_id and edge["target_id"]==target_id
