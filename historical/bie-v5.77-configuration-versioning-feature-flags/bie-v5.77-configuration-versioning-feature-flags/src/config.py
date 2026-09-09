from canonical import digest

def config_snapshot(config_id,version,values,
                    schema_version="1",metadata=None):
    return {"config_id":config_id,"version":version,
            "schema_version":schema_version,
            "values":values,"metadata":metadata or {},
            "digest":digest({"version":version,"values":values,
                             "schema_version":schema_version})}
