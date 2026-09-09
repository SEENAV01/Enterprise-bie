def freshness_status(document_version, current_version):
    if document_version==current_version:return "CURRENT"
    if document_version<current_version:return "STALE"
    return "FUTURE"

def source_allowed(status, allow_stale=False):
    return status=="CURRENT" or (allow_stale and status=="STALE")
