def field(name, data_type, required=False,
         semantic_type=None, description=None):
    return {"name":name,"data_type":data_type,
            "required":required,"semantic_type":semantic_type,
            "description":description}

def required(record):
    return record["required"]
