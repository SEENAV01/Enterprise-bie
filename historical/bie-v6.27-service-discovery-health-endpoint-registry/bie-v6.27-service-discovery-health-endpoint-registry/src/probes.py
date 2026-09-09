def probe(endpoint_id,kind="READINESS",
          interval_seconds=10,
          timeout_seconds=3):
    if kind not in {"READINESS","LIVENESS","STARTUP"}:
        raise ValueError("INVALID_PROBE_KIND")
    return {"endpoint_id":endpoint_id,
            "kind":kind,
            "interval_seconds":interval_seconds,
            "timeout_seconds":timeout_seconds}

def probe_valid(record):
    return record["interval_seconds"] > 0 and record["timeout_seconds"] > 0
