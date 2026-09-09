def diagram_spec(asset_id, diagram_type, nodes=None,
                 edges=None, labels=None, equations=None):
    return {
        "asset_id": asset_id, "diagram_type": diagram_type,
        "nodes": nodes or [], "edges": edges or [],
        "labels": labels or [], "equations": equations or []
    }

def valid(item):
    return bool(item["asset_id"] and item["diagram_type"])
