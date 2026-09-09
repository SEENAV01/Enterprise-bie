def equation_spec(asset_id, latex, semantic_meaning=None,
                   variables=None):
    if not latex:
        raise ValueError("EQUATION_REQUIRES_LATEX")
    return {
        "asset_id": asset_id, "latex": latex,
        "semantic_meaning": semantic_meaning,
        "variables": variables or []
    }

def valid(item):
    return bool(item["asset_id"] and item["latex"])
