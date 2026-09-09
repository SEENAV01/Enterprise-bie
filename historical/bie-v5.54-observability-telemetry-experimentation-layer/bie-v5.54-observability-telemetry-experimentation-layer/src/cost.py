def cost_record(record_id,entity_ref,currency="USD",
                amount=0,resource=None,provider=None):
    return {"record_id":record_id,"entity_ref":entity_ref,
            "currency":currency,"amount":amount,
            "resource":resource,"provider":provider}

def latency_record(entity_ref,duration_ms,stage=None):
    return {"entity_ref":entity_ref,"duration_ms":duration_ms,
            "stage":stage}
