def index_definition(name,
                    fields,
                    index_type="INVERTED",
                    version=1):
    if index_type not in {"INVERTED","COMPOSITE",
                          "VECTOR","KEYWORD"}:
        raise ValueError("INVALID_INDEX_TYPE")
    return {"name":name,
            "fields":fields,
            "index_type":index_type,
            "version":version}

def indexes_field(record,field):
    return field in record["fields"]
