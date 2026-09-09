def visual_asset(asset_id,asset_type,concept_refs=None,
                 source_refs=None,reusable=True,metadata=None):
    return {"asset_id":asset_id,"asset_type":asset_type,
            "concept_refs":concept_refs or [],
            "source_refs":source_refs or [],
            "reusable":reusable,"metadata":metadata or {}}
