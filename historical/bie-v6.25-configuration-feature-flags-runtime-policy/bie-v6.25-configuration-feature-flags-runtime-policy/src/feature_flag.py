def feature_flag(key,default=False,
                description=None):
    return {"key":key,"default":default,
            "description":description}

def enabled(record,value=None):
    return record["default"] if value is None else bool(value)
