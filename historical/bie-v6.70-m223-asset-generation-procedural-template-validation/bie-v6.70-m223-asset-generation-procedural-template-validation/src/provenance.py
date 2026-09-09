def provenance(asset_id,source_type,generator=None,
               template_id=None,seed=None):
    return {"asset_id":asset_id,"source_type":source_type,
            "generator":generator,"template_id":template_id,"seed":seed}
