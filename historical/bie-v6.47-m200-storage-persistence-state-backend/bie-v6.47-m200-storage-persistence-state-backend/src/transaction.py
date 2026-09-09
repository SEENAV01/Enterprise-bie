def transaction(tx_id, isolation="READ_COMMITTED",
                operations=None):
    return {"tx_id":tx_id,"isolation":isolation,
            "operations":operations or [],
            "status":"OPEN"}

def add(record, operation):
    out=dict(record)
    out["operations"]=list(record["operations"])+[operation]
    return out
