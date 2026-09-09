def index_definition(name,fields,
                    unique=False,
                    version=1):
    return {"name":name,"fields":fields,
            "unique":unique,"version":version,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
