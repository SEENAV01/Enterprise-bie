from asset_types import ASSET_SOURCES

PREFERENCE={
"diagram":["BOOK_EXTRACTED","BOOK_RECONSTRUCTED","VECTOR_GENERATED","REMOTION_NATIVE"],
"equation":["BOOK_EXTRACTED","VECTOR_GENERATED","REMOTION_NATIVE"],
"photo":["BOOK_EXTRACTED","EXTERNAL_GENERATED"],
"chart":["BOOK_EXTRACTED","VECTOR_GENERATED","REMOTION_NATIVE"],
"ui":["VECTOR_GENERATED","REMOTION_NATIVE"],
"generic":["LIBRARY_REUSABLE","VECTOR_GENERATED","REMOTION_NATIVE"]
}

def resolve(req, available_assets):
    role=req.get("role","generic")
    prefs=req.get("source_preference") or PREFERENCE.get(role,PREFERENCE["generic"])
    for source in prefs:
        matches=[a for a in available_assets if a.get("source")==source and a.get("role")==role]
        if matches:
            req["selected_source"]=source
            req["selected_asset_id"]=matches[0]["asset_id"]
            req["license_status"]=matches[0].get("license_status","UNKNOWN")
            return req
    req["selected_source"]="REMOTION_NATIVE"
    req["selected_asset_id"]=None
    req["license_status"]="N/A"
    req["fallbacks"]=prefs
    return req
