def unit_of_work(uow_id, tx_id, operations=None):
    return {"uow_id":uow_id,"tx_id":tx_id,
            "operations":operations or [],
            "status":"ACTIVE"}

def add_operation(record, operation):
    out=dict(record)
    out["operations"]=list(record["operations"])+[operation]
    return out
