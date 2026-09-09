def semantic_contract(contract_id, resource_id,
                      schema_version, invariants=None,
                      producer=None, consumers=None):
    return {"contract_id":contract_id,"resource_id":resource_id,
            "schema_version":schema_version,
            "invariants":invariants or [],
            "producer":producer,"consumers":consumers or [],
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
