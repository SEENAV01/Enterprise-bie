def semantic_type(name, base_type,
                 namespace=None, description=None):
    return {"name":name,"base_type":base_type,
            "namespace":namespace,"description":description}

def matches(record, name):
    return record["name"]==name
