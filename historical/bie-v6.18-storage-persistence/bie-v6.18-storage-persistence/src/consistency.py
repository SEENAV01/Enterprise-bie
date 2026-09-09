def consistency_contract(entity_name,
                        read="STRONG",
                        write="STRONG"):
    return {"entity":entity_name,
            "read":read,
            "write":write}

def compatible(record,allowed):
    return (record["read"] in allowed and
            record["write"] in allowed)
