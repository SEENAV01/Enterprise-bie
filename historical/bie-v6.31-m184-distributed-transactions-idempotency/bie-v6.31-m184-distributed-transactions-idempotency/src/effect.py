def effect(effect_id,idempotency_key,
           operation,result=None):
    return {"effect_id":effect_id,
            "idempotency_key":idempotency_key,
            "operation":operation,
            "result":result,
            "status":"APPLIED"}

def applied(record):
    return record["status"]=="APPLIED"
