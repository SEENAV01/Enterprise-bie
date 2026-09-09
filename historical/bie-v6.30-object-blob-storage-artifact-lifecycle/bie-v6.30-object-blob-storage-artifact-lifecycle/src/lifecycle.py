def lifecycle_transition(source,
                         target,
                         condition=None):
    allowed={"STANDARD","INFREQUENT","ARCHIVE","DELETED"}
    if source not in allowed or target not in allowed:
        raise ValueError("INVALID_STORAGE_CLASS")
    return {"source":source,"target":target,
            "condition":condition}

def applies(record):
    return record["source"]!=record["target"]
