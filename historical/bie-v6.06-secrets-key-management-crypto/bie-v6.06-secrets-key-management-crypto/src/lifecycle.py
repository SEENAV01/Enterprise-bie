STATES={"PENDING","ACTIVE","EXPIRED",
        "REVOKED","ROTATING"}

def lifecycle(material_id,state,
              version,changed_at,reason=None):
    if state not in STATES:
        raise ValueError("INVALID_MATERIAL_STATE")
    return {"material_id":material_id,
            "state":state,"version":version,
            "changed_at":changed_at,"reason":reason}

def usable(record,now=None):
    return record.get("state")=="ACTIVE"
