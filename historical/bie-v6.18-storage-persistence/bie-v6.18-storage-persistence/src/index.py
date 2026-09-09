def index(name,entity_name,
          fields,unique=False):
    return {"name":name,
            "entity":entity_name,
            "fields":fields,
            "unique":unique}

def covers(record,fields):
    return all(f in record["fields"] for f in fields)
