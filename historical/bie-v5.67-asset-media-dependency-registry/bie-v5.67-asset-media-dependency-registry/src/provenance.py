def provenance(source_refs=None,created_by=None,
               transformations=None,created_at=None):
    return {"source_refs":source_refs or [],
            "created_by":created_by,
            "transformations":transformations or [],
            "created_at":created_at}

def transformation(name,version,parameters=None):
    return {"name":name,"version":version,
            "parameters":parameters or {}}
