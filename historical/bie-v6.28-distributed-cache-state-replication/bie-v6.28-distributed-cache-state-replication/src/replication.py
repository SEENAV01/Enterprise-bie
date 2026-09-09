def replication_config(mode="ASYNC",
                      replicas=2,
                      max_lag_seconds=None):
    if mode not in {"SYNC","ASYNC"}:
        raise ValueError("INVALID_REPLICATION_MODE")
    if replicas < 1:
        raise ValueError("INVALID_REPLICA_COUNT")
    return {"mode":mode,"replicas":replicas,
            "max_lag_seconds":max_lag_seconds}

def within_lag(record,lag_seconds):
    return record["max_lag_seconds"] is None or lag_seconds <= record["max_lag_seconds"]
