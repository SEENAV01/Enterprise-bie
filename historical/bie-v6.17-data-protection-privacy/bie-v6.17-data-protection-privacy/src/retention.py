def retention_policy(resource,
                     retain_until,
                     legal_hold=False,
                     reason=None):
    return {"resource":resource,
            "retain_until":retain_until,
            "legal_hold":legal_hold,
            "reason":reason}

def deletable(record,now):
    return now >= record["retain_until"] and not record["legal_hold"]
