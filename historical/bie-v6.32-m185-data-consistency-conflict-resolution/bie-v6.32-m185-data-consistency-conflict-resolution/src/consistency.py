def consistency_contract(mode="EVENTUAL",
                         read_repair=False):
    if mode not in {"EVENTUAL","CAUSAL","BOUNDED_STALENESS","STRONG"}:
        raise ValueError("INVALID_CONSISTENCY_MODE")
    return {"mode":mode,"read_repair":read_repair}

def allows_read(record,stale_seconds=0):
    if record["mode"]=="STRONG": return stale_seconds==0
    return True
