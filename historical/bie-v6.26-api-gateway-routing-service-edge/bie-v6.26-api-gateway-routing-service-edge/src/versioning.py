def api_version(name,strategy="HEADER",
                value=None,default=False):
    if strategy not in {"HEADER","PATH","QUERY","MEDIA_TYPE"}:
        raise ValueError("INVALID_VERSION_STRATEGY")
    return {"name":name,"strategy":strategy,
            "value":value,"default":default}

def selected(record,present=None):
    return record["default"] if present is None else present==record["value"]
