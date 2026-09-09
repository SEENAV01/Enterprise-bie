def prerequisite(edge_id, prerequisite_id, target_id,
                 evidence_ids=None, confidence=1.0):
    return {"edge_id":edge_id,"prerequisite":prerequisite_id,
            "target":target_id,"relation":"PREREQUISITE",
            "evidence_ids":evidence_ids or [],"confidence":confidence}

def valid(edge):
    return edge["relation"]=="PREREQUISITE" and bool(edge["prerequisite"]) and bool(edge["target"])
