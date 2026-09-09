def index(resource, fields, index_type="STANDARD"):
    if index_type not in {"STANDARD","UNIQUE","FULLTEXT"}:
        raise ValueError("INVALID_INDEX_TYPE")
    return {"resource":resource,"fields":fields,
            "index_type":index_type,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
