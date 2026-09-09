def entity(name, fields,
           tenant_scoped=True,
           versioned=False):
    return {"name":name,
            "fields":fields,
            "tenant_scoped":tenant_scoped,
            "versioned":versioned}

def has_field(record,field):
    return field in record["fields"]
