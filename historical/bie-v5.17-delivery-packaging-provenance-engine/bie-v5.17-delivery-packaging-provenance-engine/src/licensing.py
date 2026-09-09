def license_record(asset_id,license_name,source_url=None,
                   attribution=None,restrictions=None):
    return {"asset_id":asset_id,"license":license_name,
            "source_url":source_url,"attribution":attribution,
            "restrictions":restrictions or []}

def validate_licenses(assets):
    errors=[]
    for a in assets:
        if not a.get("license"):
            errors.append("LICENSE_MISSING:"+a.get("asset_id","UNKNOWN"))
    return {"valid":not errors,"errors":errors}
