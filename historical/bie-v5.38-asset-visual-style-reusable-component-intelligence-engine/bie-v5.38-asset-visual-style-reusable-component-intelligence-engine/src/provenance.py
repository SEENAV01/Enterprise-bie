def asset_provenance(asset_id,source_refs=None,creation_method=None,
                    license_ref=None):
    return {"asset_id":asset_id,"source_refs":source_refs or [],
            "creation_method":creation_method,"license_ref":license_ref}
