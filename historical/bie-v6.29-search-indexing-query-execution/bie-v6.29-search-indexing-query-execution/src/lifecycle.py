def index_lifecycle(name,
                   state="ACTIVE",
                   generation=1):
    if state not in {"BUILDING","ACTIVE","REBUILDING",
                     "DRAINING","DELETED"}:
        raise ValueError("INVALID_INDEX_STATE")
    return {"name":name,"state":state,
            "generation":generation}

def queryable(record):
    return record["state"]=="ACTIVE"
