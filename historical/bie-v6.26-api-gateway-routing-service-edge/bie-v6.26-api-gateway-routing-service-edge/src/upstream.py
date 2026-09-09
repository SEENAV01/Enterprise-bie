def upstream(name,endpoints,
             strategy="ROUND_ROBIN"):
    if strategy not in {"ROUND_ROBIN","LEAST_CONNECTIONS",
                        "WEIGHTED","HASH"}:
        raise ValueError("INVALID_UPSTREAM_STRATEGY")
    return {"name":name,"endpoints":endpoints,
            "strategy":strategy}

def choose(record,index=0):
    if not record["endpoints"]:
        raise ValueError("NO_UPSTREAM")
    return record["endpoints"][index % len(record["endpoints"])]
