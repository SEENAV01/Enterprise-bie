def index_alias(name,target,
               write=False):
    return {"name":name,"target":target,
            "write":write}

def resolves(record):
    return bool(record["target"])
