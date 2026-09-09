LEVELS={"EVENTUAL","CAUSAL","STRONG"}

def consistency_contract(scope,
                         level,
                         read_your_writes=False,
                         monotonic_reads=False):
    if level not in LEVELS:
        raise ValueError("INVALID_CONSISTENCY_LEVEL")
    return {"scope":scope,"level":level,
            "read_your_writes":read_your_writes,
            "monotonic_reads":monotonic_reads}
