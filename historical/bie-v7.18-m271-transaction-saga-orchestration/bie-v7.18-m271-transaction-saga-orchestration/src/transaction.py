def begin(tx_id):
    return {"tx_id":tx_id,"status":"ACTIVE","effects":[]}

def record_effect(tx,effect):
    tx["effects"].append(effect)
    return tx

def commit(tx):
    tx["status"]="COMMITTED"
    return tx

def rollback(tx):
    tx["status"]="ROLLED_BACK"
    return tx
