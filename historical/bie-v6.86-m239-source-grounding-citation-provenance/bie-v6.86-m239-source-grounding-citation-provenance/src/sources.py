def source(source_id,uri,title="",publisher="",locator=None):
    return {"source_id":source_id,"uri":uri,"title":title,"publisher":publisher,
            "locator":locator}

def validate_source(s):
    errors=[]
    if not s.get("source_id"): errors.append("MISSING_SOURCE_ID")
    if not s.get("uri"): errors.append("MISSING_URI")
    return {"passed":not errors,"errors":errors}
