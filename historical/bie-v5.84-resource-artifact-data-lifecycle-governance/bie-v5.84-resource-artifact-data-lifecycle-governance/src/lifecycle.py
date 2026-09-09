def lifecycle_state(action):
    mapping={"RETAIN":"ACTIVE","ARCHIVE":"ARCHIVED",
             "DELETE":"DELETED"}
    if action not in mapping: raise ValueError("INVALID_LIFECYCLE_ACTION")
    return mapping[action]

def apply_lifecycle(record,action):
    out=dict(record); out["lifecycle_state"]=lifecycle_state(action)
    return out
