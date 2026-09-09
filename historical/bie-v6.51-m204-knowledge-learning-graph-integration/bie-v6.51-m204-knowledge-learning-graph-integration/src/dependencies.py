def dependency(edge_id, source, target, relation="DEPENDS_ON",
              evidence_ids=None, confidence=1.0):
    return {"edge_id":edge_id,"source":source,"target":target,
            "relation":relation,"evidence_ids":evidence_ids or [],
            "confidence":confidence}

def valid(edge):
    return bool(edge["source"]) and bool(edge["target"]) and bool(edge["relation"])
