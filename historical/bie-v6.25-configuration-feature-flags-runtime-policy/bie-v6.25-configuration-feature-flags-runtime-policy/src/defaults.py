def default(key,value,value_type="string"):
    return {"key":key,"value":value,"value_type":value_type}

def resolve(explicit,default_value):
    return explicit if explicit is not None else default_value
