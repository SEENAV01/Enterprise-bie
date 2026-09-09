from identity import stable_hash

def build_record(build_id,git_ref=None,renderer_version=None,
                 engine_version=None,config=None):
    record={"build_id":build_id,"git_ref":git_ref,
            "renderer_version":renderer_version,
            "engine_version":engine_version,"config":config or {}}
    record["build_fingerprint"]=stable_hash(record)
    return record
