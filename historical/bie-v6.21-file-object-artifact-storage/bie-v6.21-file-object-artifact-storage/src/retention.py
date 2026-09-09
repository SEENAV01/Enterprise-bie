def retention(object_id,
             retain_until,
             legal_hold=False):
    return {"object_id":object_id,
            "retain_until":retain_until,
            "legal_hold":legal_hold}

def deletable(record,now):
    return now >= record["retain_until"] and not record["legal_hold"]
