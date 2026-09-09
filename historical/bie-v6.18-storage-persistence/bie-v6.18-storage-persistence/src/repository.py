def repository(name, entity_name,
               consistency="STRONG"):
    if consistency not in {"STRONG","EVENTUAL"}:
        raise ValueError("INVALID_CONSISTENCY")
    return {"name":name,
            "entity":entity_name,
            "consistency":consistency}

def contract(record):
    return {"repository":record["name"],
            "entity":record["entity"],
            "consistency":record["consistency"]}
