def transformation(transform_id, operation,
                     version=None, actor=None):
    return {"transform_id":transform_id,"operation":operation,
            "version":version,"actor":actor}

def versioned(record):
    return record["version"] is not None
