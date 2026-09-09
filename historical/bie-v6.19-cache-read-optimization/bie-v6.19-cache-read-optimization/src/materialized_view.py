def materialized_view(name,
                    source_entities,
                    refresh_mode="EVENT"):
    if refresh_mode not in {"EVENT","SCHEDULED",
                            "ON_DEMAND"}:
        raise ValueError("INVALID_REFRESH_MODE")
    return {"name":name,
            "source_entities":source_entities,
            "refresh_mode":refresh_mode,
            "status":"ACTIVE"}

def refresh(record):
    out=dict(record); out["last_action"]="REFRESH"; return out
