def query(resource, filters=None, projection=None,
         sort=None, page=None, consistency=None):
    return {"resource":resource,"filters":filters or [],
            "projection":projection or ["*"],"sort":sort or [],
            "page":page,"consistency":consistency}

def valid(record):
    return bool(record["resource"])
