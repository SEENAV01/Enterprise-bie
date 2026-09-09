def specification(spec_id, asset_id, generation_method,
                  dimensions=None, format=None, style=None,
                  constraints=None):
    return {
        "spec_id": spec_id, "asset_id": asset_id,
        "generation_method": generation_method,
        "dimensions": dimensions, "format": format,
        "style": style, "constraints": constraints or {}
    }

def valid(item):
    return bool(item["spec_id"] and item["asset_id"] and
                item["generation_method"])
