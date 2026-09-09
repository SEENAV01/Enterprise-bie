def query(entity_name,
         filters=None,sort=None,
         limit=None):
    return {"entity":entity_name,
            "filters":filters or {},
            "sort":sort or [],
            "limit":limit}

def matches(record,filters):
    return all(record.get(k)==v
               for k,v in filters.items())
