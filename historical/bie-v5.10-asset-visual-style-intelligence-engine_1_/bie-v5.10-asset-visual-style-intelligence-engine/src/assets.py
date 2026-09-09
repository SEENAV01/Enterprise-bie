def asset(asset_id, asset_type, semantic_role, version="1.0",
          source=None, variants=None):
    return {
      "asset_id":asset_id,"asset_type":asset_type,
      "semantic_role":semantic_role,"version":version,
      "source":source,"variants":variants or []
    }

def asset_reference(asset_id, required_variant=None):
    return {"asset_id":asset_id,"required_variant":required_variant}
