def validate_ingestion(result):
    errors=[]
    if not result.get("source",{}).get("source_id"): errors.append("MISSING_SOURCE_ID")
    if not result.get("document",{}).get("document_id"): errors.append("MISSING_DOCUMENT_ID")
    for c in result.get("chunks",[]):
        if not c.get("text"): errors.append("EMPTY_CHUNK")
    return {"valid":not errors,"errors":errors}
