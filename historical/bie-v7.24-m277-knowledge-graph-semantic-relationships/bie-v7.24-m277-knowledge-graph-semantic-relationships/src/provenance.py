def provenance(source_id, source_version, locator=None):
    return {"source_id":source_id,"source_version":source_version,"locator":locator}

def validate_provenance(item):
    return bool(item.get("source_id") and item.get("source_version"))
