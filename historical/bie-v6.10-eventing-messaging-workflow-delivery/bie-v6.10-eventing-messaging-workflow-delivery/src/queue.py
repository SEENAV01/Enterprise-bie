def queue(name,delivery="AT_LEAST_ONCE",
         max_depth=None):
    return {"name":name,
            "delivery":delivery,
            "max_depth":max_depth}

def can_enqueue(record,depth):
    limit=record.get("max_depth")
    return limit is None or depth < limit
