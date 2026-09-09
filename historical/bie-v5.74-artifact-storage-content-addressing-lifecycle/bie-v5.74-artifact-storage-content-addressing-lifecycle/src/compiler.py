from identity import artifact_id

def compile_storage(data,metadata=None):
    aid=artifact_id(data)
    return {"schema_version":"5.74",
            "artifact_id":aid,
            "content_hash":aid.split(":",1)[1],
            "metadata":metadata or {},
            "quality_gate":{"valid":True,"errors":[]}}
