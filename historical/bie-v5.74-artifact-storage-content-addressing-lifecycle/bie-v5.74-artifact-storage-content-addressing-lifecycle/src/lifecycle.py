STATES=("STAGED","VALIDATED","PROMOTED",
        "RELEASED","ARCHIVED","GC_ELIGIBLE","DELETED")

ALLOWED={
 "STAGED":{"VALIDATED","GC_ELIGIBLE"},
 "VALIDATED":{"PROMOTED","GC_ELIGIBLE"},
 "PROMOTED":{"RELEASED","ARCHIVED"},
 "RELEASED":{"ARCHIVED"},
 "ARCHIVED":{"GC_ELIGIBLE"},
 "GC_ELIGIBLE":{"DELETED"}
}

def transition(current,target):
    if current not in STATES or target not in STATES:
        raise ValueError("UNKNOWN_LIFECYCLE_STATE")
    if target not in ALLOWED.get(current,set()):
        raise ValueError("INVALID_LIFECYCLE_TRANSITION")
    return target
