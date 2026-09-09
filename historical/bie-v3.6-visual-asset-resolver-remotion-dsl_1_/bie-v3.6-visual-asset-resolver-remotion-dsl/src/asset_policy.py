def validate_asset(asset):
    errors=[]
    if asset.get("selected_source") in ["EXTERNAL_GENERATED","LIBRARY_REUSABLE"] and asset.get("license_status")=="UNKNOWN":
        errors.append("LICENSE_UNKNOWN")
    if asset.get("selected_source")=="BOOK_EXTRACTED" and not asset.get("evidence_ids"):
        errors.append("BOOK_ASSET_WITHOUT_EVIDENCE")
    return {"valid":not errors,"errors":errors}

def choose_generation_fallback(req):
    return {
      "asset_id":req["asset_id"],
      "role":req["role"],
      "fallback":"VECTOR_GENERATED" if req["role"] in ["diagram","chart","equation","ui"] else "EXTERNAL_GENERATED",
      "requires_review":True
    }
