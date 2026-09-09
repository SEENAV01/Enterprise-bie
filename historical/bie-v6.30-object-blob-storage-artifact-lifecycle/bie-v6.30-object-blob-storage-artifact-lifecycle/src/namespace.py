def namespace(name,tenant=None,
              region=None):
    return {"name":name,"tenant":tenant,
            "region":region}

def scoped(record):
    return bool(record["name"])
